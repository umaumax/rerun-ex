#!/usr/bin/env python3

import asyncio

import streamlit as st

st.set_page_config(
    page_title="Streamlit Dashboard App",
    layout="wide",
    initial_sidebar_state="collapsed")

st.title('Streamlit Dashboard')

slate = st.empty()
body = slate.container()


def cleanup():
    print('[🧹] cleanup')
    slate.empty()


app_col = body.empty()
app_container = app_col.container()

if "count" not in st.session_state:
    st.session_state.count = 0
else:
    st.session_state.count += 1


async def rerun_app(container):
    inner_container = container.container()
    rerun_button_flag = False
    rerun_reset_button_flag = False
    rerun_stop_button_flag = False
    with inner_container:
        rerun_status_placeholder = inner_container.empty()
        # TODO: update url
        st.link_button("🔗 Go to rerun web page",
                       "http://localhost:8080/?url=ws://localhost:9877")
        if st.button("🔃 Reset rerun"):
            rerun_reset_button_flag = True
        if st.button("🛑 Stop rerun"):
            rerun_stop_button_flag = True
        st.header("commands")
        if st.button("▶️ Run rerun sample"):
            rerun_button_flag = True
        st.write('memory and cpu samples')

    async def rerun():
        try:
            recording_id = f'record-{st.session_state.count}'

            def generate_shell_script(main_script):
                return f'''
                cleanup() {{
                  exit_code=$?
                  pkill -P $$
                  exit $exit_code
                }}
                trap cleanup SIGINT SIGTERM
                {main_script}
                BACKGROUND_PID=$!
                wait $BACKGROUND_PID
                trap - SIGINT SIGTERM
                '''
            command1 = generate_shell_script(f'''
            python3 -c $'import psutil; import time;\nprint("id,",",".join(map(str,range(psutil.cpu_count(logical=False)))));\ni=0\nwhile True: print(i,",",",".join(map(str,psutil.cpu_percent(percpu=True))), flush=True); time.sleep(0.1); i+=1' \
                | ./csv-pipe-rerun.py --recording_id {recording_id} -t cpu --addr 127.0.0.1:9876 \
                &
            ''')
            command2 = generate_shell_script(f'''
            python3 -c $'import psutil; import time;\nprint("id,used,free");\ni=0\nwhile True: memory_info = psutil.virtual_memory(); memory_used = memory_info.used / (1024 ** 2); memory_free = memory_info.free / (1024 ** 2); print(i, ",", memory_used, ",", memory_free, flush=True); time.sleep(0.1); i+=1' \
              | ./csv-pipe-rerun.py --recording_id {recording_id} -t memory --addr 127.0.0.1:9876 \
              &
            ''')
            inner_container.write("running...")
            result1, result2 = await asyncio.gather(run_command_async(command1), run_command_async(command2))
            inner_container.write("asyncio result:")
            inner_container.code(result1, language="bash")
            inner_container.code(result2, language="bash")
        except asyncio.CancelledError as e:
            raise e

    tasks = []
    if rerun_button_flag is True:
        tasks.append(asyncio.create_task(rerun()))

    rerun_stop_command = f'''
    SESSION_LINE=$(screen -list | grep "\\.RERUN_SESSION" | head -n 1)
    if [[ -n "$SESSION_LINE" ]]; then
      SESSION_PID=$(printf "%s" "$SESSION_LINE" | grep -E -o "[0-9]+\\.RERUN_SESSION" | grep -E -o "[0-9]+")
      pkill -P "$SESSION_PID"
      screen -S "RERUN_SESSION" -X quit
    fi
    '''
    # TODO: parameterize rerun server args
    rerun_start_command = f'''
    screen -dmS "RERUN_SESSION" "bash" "-c" "python3 -m rerun --serve --web-viewer-port 8080 --ws-server-port 9877 --port 9876 & wait"
    '''
    if rerun_reset_button_flag is True:
        command = f'''
        set -x
        {rerun_stop_command}
        {rerun_start_command}
        '''
        result, = await asyncio.gather(run_command_async(command))
        inner_container.write("🔃 reset rerun result:")
        inner_container.code(result, language="bash")
    if rerun_stop_button_flag is True:
        command = f'''
        set -x
        {rerun_stop_command}
        '''
        result, = await asyncio.gather(run_command_async(command))
        inner_container.write("🛑 stop rerun result:")
        inner_container.code(result, language="bash")

    async def check_rerun_process_status():
        while True:
            command = f'''
            if screen -list | grep -q "\\.RERUN_SESSION"; then
              echo "✅️ Running..."
            else
              echo "❌️ Something wrong..."
              screen -ls
            fi
            '''
            result, = await asyncio.gather(run_command_async(command))

            rerun_status_placeholder.empty()
            with rerun_status_placeholder.container():
                st.write("⚙️ rerun status:")
                st.code(result, language="bash")
            await asyncio.sleep(0.5)
    tasks.append(asyncio.create_task(check_rerun_process_status()))

    head_placeholder = inner_container.empty()
    while True:
        head_placeholder.empty()
        with head_placeholder.container():
            pass
        await asyncio.sleep(1.0)
    await asyncio.gather(*tasks)


async def run_command_async(command):
    # WARN: use asyncio.create_subprocess_exec
    result = await asyncio.create_subprocess_shell(command, stdout=asyncio.subprocess.PIPE)

    try:
        output, _ = await result.communicate()
        return output.decode()
    except asyncio.CancelledError as e:
        result.terminate()
        raise e


async def main():
    print('[💡] main called')
    tasks = []
    tasks.append(asyncio.create_task(rerun_app(app_container)))
    await asyncio.gather(*tasks)

if __name__ == '__main__':
    asyncio.run(main())
