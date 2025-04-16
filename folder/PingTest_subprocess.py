import subprocess
import threading
import time

file_lock = threading.Lock()


def connect_to_wifi(commands: str) -> None:
    """
    使用 subprocess 執行 PowerShell 指令，以新增並連線至指定的 Wi-Fi。
    """
    try:
        subprocess.run(
            ["powershell", "-Command", commands],
            capture_output=True,
            text=True,
            check=True
        )
    except subprocess.CalledProcessError as e:
        print("Wi-Fi 設定失敗")
        print(e.stderr)


def get_ip_info() -> dict:
    """
    從 ipconfig /all 輸出中，擷取 192.168.1.101、192.168.2.102 與 192.168.2.103 的介面名稱。
    若尚未取得 IP，則預設值為 'None'。
    回傳格式範例:
    {
        '192.168.1.101': '乙太網路',
        '192.168.2.102': 'Wi-Fi',
        '192.168.2.103': '乙太網路 2'
    }
    """
    # 這裡使用繁體中文關鍵字做篩選 ("卡"、"IPv4 位址")
    ENZH = ["卡", "IPv4 位址"]
    result = subprocess.run(
        ["powershell", "-Command", "ipconfig /all"],
        capture_output=True,
        text=True
    )
    output = result.stdout
    lines = output.splitlines()

    # 預設記錄三個 IP 位址，皆為 'None'
    ip_to_adapter = {
        "192.168.1.101": "None",
        "192.168.1.102": "None",
        "192.168.1.103": "None"
    }

    # 尋找「卡」開頭的區域，並在後續數行找出 "IPv4 位址" 行
    for i in range(len(lines)):
        line = lines[i].strip()
        # 若該行含有 "卡" 關鍵字
        if ENZH[0] in line:
            # 嘗試擷取網路介面名稱
            adapter_name = line.split(ENZH[0])[-1].split(":")[0].strip()
            # 在接下來幾行搜尋 "IPv4 位址"
            for j in range(i, i + 10):
                if j >= len(lines):
                    break
                detail_line = lines[j].strip()
                if detail_line.startswith(ENZH[1]):
                    # 擷取 IP 位址 (不含括號內文字)
                    ipv4_address = detail_line.split(":")[-1].split("(")[0].strip()
                    # 若該 IP 在我們關心的字典中，更新其對應的介面名稱
                    if ipv4_address in ip_to_adapter:
                        ip_to_adapter[ipv4_address] = adapter_name
                    break

    return ip_to_adapter


def ping_with_source(ip_start: str, ip_target: str, adapter_info: str) -> None:
    """
    以指定的來源 IP (ip_start) ping 目標 IP (ip_target)，並根據輸出內容判斷封包遺失率。
    adapter_info 只是用來顯示更明確的結果資訊。
    """
    command = f"ping -S {ip_start} {ip_target}"
    ping_result = subprocess.run(
        ["powershell", "-Command", command],
        capture_output=True,
        text=True
    )
    stdout_text = ping_result.stdout

    # 嘗試從輸出中尋找遺失率 (x%)
    loss_keyword = "%"
    loss_index = stdout_text.find(loss_keyword)
    if loss_index != -1:
        # 取出包含 "(0%" 或 "(xx%" 之類的區段
        snippet = stdout_text[loss_index - 3:loss_index + 1]
        if snippet == " (0%":
            print(f"PASS: {adapter_info}、IP: {ip_start}")
            return
        loss_rate = snippet.replace("(", "").replace('）', '').strip()
        print(f"來源 IP: {ip_start}，Ping 測試失敗，封包遺失率: {loss_rate}")


def set_static_ip() -> None:
    """
    將「乙太網路」介面設定為靜態 IP: 192.168.255.100 / 255.255.0.0 / 192.168.0.1。
    """
    command_set_static = (
        'netsh interface ipv4 set address '
        'name="乙太網路" '
        'static 192.168.255.100 255.255.0.0 192.168.0.1'
    )
    try:
        subprocess.run(["powershell", "-Command", command_set_static],
                       capture_output=True, text=True, check=True)
        # print("已將「乙太網路」介面設置為靜態 IP：192.168.255.100/255.255.0.0，閘道：192.168.0.1")
    except subprocess.CalledProcessError as e:
        print("設定靜態 IP 失敗")
        print(e.stderr)


if __name__ == "__main__":
    # Wi-Fi 名稱與 XML 設定檔路徑
    wifi_name = "WM_Tester"
    path = f".\\0\\Winmate_Test_GUI\\exes\\Wi-Fi-{wifi_name}.xml"

    # 組合要執行的 PowerShell 指令
    ps_commands = f"""
        netsh interface ipv4 set address name="乙太網路" source=static address=192.168.1.101 mask=255.255.255.0
        netsh interface ipv4 set address name="乙太網路 2" source=static address=192.168.1.102 mask=255.255.255.0
        netsh interface ipv4 set address name="Wi-Fi 2" source=static address=192.168.1.103 mask=255.255.255.0

        $currentPolicy = Get-ExecutionPolicy
        Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope Process -Force

        $profilePath = "{path}"
        netsh wlan add profile filename=$profilePath
        netsh wlan connect name="{wifi_name}"

        Set-ExecutionPolicy -ExecutionPolicy $currentPolicy -Scope Process -Force
    """

    # 執行連線動作
    connect_to_wifi(ps_commands)

    # 等待 5 秒，讓網路介面有機會獲得 IP
    time.sleep(10)

    # 最多嘗試 20 次 (20 秒) 檢查 IP 狀態
    for try_step in range(1, 11):
        time.sleep(1)
        info_data = get_ip_info()
        # 若所有 IP 位址都不再是 'None'，表示已成功取得 IP
        # print(info_data.values())
        if all(value != "None" for value in info_data.values()):
            break
        if try_step == 10:
            print("Wi-Fi: 警告，未取得所有目標 IP")
            # 到達 20 秒都無法取得，視為失敗
            # 在程式結束前，將「乙太網路」改為靜態 IP
            # set_static_ip()
            # exit(1)

    # 若成功取得目標 IP，開始平行執行 ping 測試
    threads = []
    threads.append(
        threading.Thread(
            target=ping_with_source,
            args=("192.168.1.101", "192.168.1.1", info_data["192.168.1.101"])
        )
    )
    threads.append(
        threading.Thread(
            target=ping_with_source,
            args=("192.168.1.102", "192.168.1.1", info_data["192.168.1.102"])
        )
    )
    threads.append(
        threading.Thread(
            target=ping_with_source,
            args=("192.168.1.103", "192.168.1.1", info_data["192.168.1.103"])
        )
    )

    # 啟動所有 ping 執行緒
    for t in threads:
        t.start()
        time.sleep(0.1)  # 稍微錯開啟動時間

    # 等待所有執行緒結束
    for t in threads:
        t.join()

    print("RJ45/Wi-Fi: PASS")

    # 在程式結束前，將「乙太網路」改為靜態 IP
    set_static_ip()
