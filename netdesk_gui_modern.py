import tkinter as tk
from tkinter import scrolledtext, messagebox
import socket
import subprocess
import platform
import time
import csv
import json
import os
import urllib.request
import urllib.error
import urllib.parse
from datetime import datetime


# ---------- NETDESK SERVER CONNECTION ----------

def get_local_ip():
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.connect(("8.8.8.8", 80))
        ip = sock.getsockname()[0]
        sock.close()
        return ip
    except OSError:
        try:
            return socket.gethostbyname(socket.gethostname())
        except OSError:
            return "127.0.0.1"


def get_server_base_url():
    server_ip = server_entry.get().strip()
    if not server_ip:
        messagebox.showwarning("Missing Server", "Enter the NetDesk Server IP address.")
        return None
    if not server_ip.startswith(("http://", "https://")):
        server_ip = "http://" + server_ip
    return server_ip.rstrip("/") + ":8000"


def server_request(path):
    base_url = get_server_base_url()
    if not base_url:
        return None
    try:
        request = urllib.request.Request(
            base_url + path,
            headers={"User-Agent": "NetDesk-Client/1.0"}
        )
        with urllib.request.urlopen(request, timeout=4) as response:
            return response.read()
    except urllib.error.URLError as exc:
        show(f"Server connection failed: {exc}")
        return None
    except Exception as exc:
        show(f"Server error: {exc}")
        return None


def connect_server():
    clear_result()
    show("CONNECTING TO NETDESK SERVER")
    show("----------------------------------------")
    data = server_request("/status")
    if data is None:
        show("Status : Connection Failed")
        show("Check the server IP, port and LAN connection.")
        return
    try:
        status = json.loads(data.decode("utf-8"))
        show("Status     : Server Online")
        show("Server IP  : " + status.get("server_ip", "Unknown"))
        show("Server Port: " + str(status.get("port", "Unknown")))
        show("Client IP  : " + status.get("client_ip", "Unknown"))
    except Exception:
        show("Status : Invalid server response")


def view_resources():
    clear_result()
    show("NETDESK SHARED CLASSROOM RESOURCES")
    show("----------------------------------------")
    data = server_request("/resources")
    if data is None:
        show("Unable to retrieve resources.")
        return
    try:
        resources = json.loads(data.decode("utf-8"))
        found = False
        for folder, files in resources.items():
            show(f"\n[{folder.upper()}]")
            if not files:
                show("  No files available.")
                continue
            found = True
            for item in files:
                show(f"  {item.get('name')} ({item.get('size', 0)} bytes)")
        if not found:
            show("\nNo shared files are currently available.")
    except Exception as exc:
        show("Invalid resource response: " + str(exc))


def download_resource():
    folder = resource_folder_entry.get().strip()
    filename = resource_file_entry.get().strip()
    if not folder or not filename:
        messagebox.showwarning("Missing Resource", "Enter both resource folder and file name.")
        return
    clear_result()
    show("DOWNLOADING CLASSROOM RESOURCE")
    show("----------------------------------------")
    show(f"Folder : {folder}")
    show(f"File   : {filename}")
    safe_folder = urllib.parse.quote(folder, safe="")
    safe_file = urllib.parse.quote(filename, safe="")
    data = server_request(f"/resources/{safe_folder}/{safe_file}")
    if data is None:
        show("Download failed.")
        return
    try:
        downloads_dir = os.path.join(os.path.expanduser("~"), "Downloads")
        os.makedirs(downloads_dir, exist_ok=True)
        save_path = os.path.join(downloads_dir, os.path.basename(filename))
        with open(save_path, "wb") as file:
            file.write(data)
        show("\nDownload successful.")
        show("Saved to: " + save_path)
    except Exception as exc:
        show("Could not save file: " + str(exc))


# ---------- BASIC FUNCTIONS ----------

def ping(address):
    if platform.system().lower() == "windows":
        command = ["ping", "-n", "1", "-w", "1000", address]
    else:
        command = ["ping", "-c", "1", "-W", "1", address]

    start = time.perf_counter()

    result = subprocess.run(
        command,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )

    delay = (time.perf_counter() - start) * 1000

    if result.returncode == 0:
        return True, round(delay, 2)

    return False, 0


def dns_check():
    try:
        socket.gethostbyname("google.com")
        return True
    except:
        return False


def show(text=""):
    result_box.insert(tk.END, text + "\n")
    result_box.see(tk.END)
    window.update()


def clear_result():
    result_box.delete("1.0", tk.END)


# ---------- SAVE HISTORY ----------

def save_history(target, loss):

    if loss == 0:
        status = "Stable"
    elif loss <= 20:
        status = "Slightly Unstable"
    else:
        status = "Unstable"

    filename = "network_history.csv"

    try:
        with open(filename, "x", newline="") as file:
            writer = csv.writer(file)
            writer.writerow([
                "Date",
                "Time",
                "Target",
                "Packet Loss",
                "Network Status"
            ])
    except FileExistsError:
        pass

    now = datetime.now()

    with open(filename, "a", newline="") as file:
        writer = csv.writer(file)

        writer.writerow([
            now.strftime("%d-%m-%Y"),
            now.strftime("%I:%M %p"),
            target,
            str(round(loss, 2)) + "%",
            status
        ])


# ---------- TEST NETWORK ----------

def test_network():

    target = target_entry.get().strip()

    if not target:
        messagebox.showwarning(
            "Missing Target",
            "Enter a website or IP address."
        )
        return

    clear_result()

    show("Testing connection to: " + target)
    show("----------------------------------------")

    received = 0
    times = []
    packets = 5

    for number in range(1, packets + 1):

        status, delay = ping(target)

        if status:
            received += 1
            times.append(delay)
            show(
                f"Packet {number} -> Received | {delay} ms"
            )
        else:
            show(
                f"Packet {number} -> Lost"
            )

    lost = packets - received
    loss = (lost / packets) * 100

    show("\n----------------------------------------")
    show("TEST RESULT")
    show("----------------------------------------")

    show(f"Packets Sent     : {packets}")
    show(f"Packets Received : {received}")
    show(f"Packets Lost     : {lost}")
    show(f"Packet Loss      : {loss:.2f} %")

    if times:

        average = sum(times) / len(times)

        show(f"Average Response : {average:.2f} ms")
        show(f"Minimum Response : {min(times)} ms")
        show(f"Maximum Response : {max(times)} ms")

        if average < 100:
            delay_status = "Good"
        elif average <= 250:
            delay_status = "Moderate"
        else:
            delay_status = "High"

        show("Delay Status     : " + delay_status)

    else:
        show("Response Time    : Not Available")

    if loss == 0:
        network_status = "Stable"
    elif loss <= 20:
        network_status = "Slightly Unstable"
    else:
        network_status = "Unstable"

    show("Network Status   : " + network_status)

    save_history(target, loss)

    show("\nResult saved to network_history.csv")


# ---------- NETWORK DIAGNOSIS ----------

def diagnose_network():

    router = router_entry.get().strip()
    target = target_entry.get().strip()

    if not router or not target:
        messagebox.showwarning(
            "Missing Input",
            "Enter both Router IP and Target."
        )
        return

    clear_result()

    show("NETWORK DIAGNOSIS")
    show("----------------------------------------")

    router_ok, router_time = ping(router)
    internet_ok, internet_time = ping("8.8.8.8")
    dns_ok = dns_check()
    target_ok, target_time = ping(target)

    if router_ok:
        show(f"\nRouter   : Reachable | {router_time} ms")
    else:
        show("\nRouter   : Not Reachable")

    if internet_ok:
        show(f"Internet : Reachable | {internet_time} ms")
    else:
        show("Internet : Not Reachable")

    if dns_ok:
        show("DNS      : Working")
    else:
        show("DNS      : Not Working")

    if target_ok:
        show(f"Target   : Reachable | {target_time} ms")
    else:
        show("Target   : Not Reachable")

    show("\n----------------------------------------")
    show("POSSIBLE PROBLEM")
    show("----------------------------------------")

    if not router_ok:
        show("Status : Local Network Problem")
        show("Suggestion : Check Wi-Fi, cable or router.")

    elif not internet_ok:
        show("Status : Internet Connection Problem")
        show("Suggestion : Router works but Internet is unavailable.")

    elif not dns_ok:
        show("Status : DNS Problem")
        show("Suggestion : Internet works but DNS has a problem.")

    elif not target_ok:
        show("Status : Target Device Problem")
        show("Suggestion : Target may be offline.")

    else:
        show("Status : Network Working Normally")
        show("Suggestion : No major problem detected.")


# ---------- CLASSROOM DEVICES ----------

def check_devices():

    router = router_entry.get().strip()

    if not router:
        messagebox.showwarning(
            "Missing Router",
            "Enter router/default gateway IP."
        )
        return

    devices = {
        "Router": router,
        "Teacher PC": "192.168.1.10",
        "Lab Server": "192.168.1.20",
        "Printer": "192.168.1.30",
        "Smart Board": "192.168.1.40"
    }

    clear_result()

    show("CLASSROOM DEVICE STATUS")
    show("----------------------------------------")

    online = 0

    for name, ip in devices.items():

        status, delay = ping(ip)

        if status:
            show(f"{name} -> Online | {delay} ms")
            online += 1
        else:
            show(f"{name} -> Offline")

    offline = len(devices) - online

    show("\n----------------------------------------")
    show("DEVICE SUMMARY")
    show("----------------------------------------")

    show(f"Total Devices   : {len(devices)}")
    show(f"Online Devices  : {online}")
    show(f"Offline Devices : {offline}")

    if offline == 0:
        show("Classroom Status: All devices available")

    elif online == 0:
        show("Classroom Status: All devices unavailable")

    else:
        show("Classroom Status: Some devices need attention")


# ---------- VIEW HISTORY ----------

def view_history():

    clear_result()

    show("NETWORK TEST HISTORY")
    show("----------------------------------------")

    try:
        with open("network_history.csv", "r") as file:

            reader = csv.reader(file)
            rows = list(reader)

            if len(rows) <= 1:
                show("No previous test history found.")
                return

            for row in rows:
                show(" | ".join(row))

    except FileNotFoundError:
        show("No history found.")
        show("Run Test Network first.")


# ---------- MODERN GUI ----------

# UI redesign only. Networking functions above are unchanged.

BG = "#0f172a"
CARD = "#111c33"
CARD_ALT = "#16233f"
TEXT = "#e5e7eb"
MUTED = "#94a3b8"
ACCENT = "#38bdf8"
ACCENT_DARK = "#0ea5e9"
SUCCESS = "#34d399"
BORDER = "#263653"

window = tk.Tk()
window.title("NetDesk | Classroom Connectivity Assistant")
window.geometry("1080x760")
window.minsize(980, 680)
window.configure(bg=BG)


def modern_button(parent, text, command, width=18, accent=False):
    return tk.Button(
        parent, text=text, command=command, width=width,
        font=("Segoe UI", 10, "bold"),
        bg=ACCENT_DARK if accent else CARD_ALT,
        fg="#ffffff",
        activebackground=ACCENT if accent else "#203252",
        activeforeground="#ffffff",
        relief="flat", bd=0, cursor="hand2",
        padx=12, pady=9
    )


def section_title(parent, title, subtitle=None):
    frame = tk.Frame(parent, bg=CARD)
    frame.pack(fill="x", pady=(0, 10))
    tk.Label(
        frame, text=title, font=("Segoe UI", 12, "bold"),
        bg=CARD, fg=TEXT
    ).pack(anchor="w")
    if subtitle:
        tk.Label(
            frame, text=subtitle, font=("Segoe UI", 9),
            bg=CARD, fg=MUTED
        ).pack(anchor="w", pady=(2, 0))


# Header
header = tk.Frame(window, bg=BG)
header.pack(fill="x", padx=28, pady=(22, 14))

brand = tk.Frame(header, bg=BG)
brand.pack(side="left")

tk.Label(
    brand, text="NET", font=("Segoe UI", 26, "bold"),
    bg=BG, fg=ACCENT
).pack(side="left")
tk.Label(
    brand, text="DESK", font=("Segoe UI", 26, "bold"),
    bg=BG, fg=TEXT
).pack(side="left")

tk.Label(
    header, text="CLASSROOM CONNECTIVITY ASSISTANT",
    font=("Segoe UI", 9, "bold"), bg=BG, fg=MUTED
).pack(side="left", padx=(18, 0), pady=(10, 0))

status_frame = tk.Frame(header, bg=BG)
status_frame.pack(side="right")
tk.Label(
    status_frame, text="●", font=("Segoe UI", 12),
    bg=BG, fg=SUCCESS
).pack(side="left")
tk.Label(
    status_frame, text=" LAN CLIENT",
    font=("Segoe UI", 9, "bold"), bg=BG, fg=MUTED
).pack(side="left")


# Main two-column layout
main = tk.Frame(window, bg=BG)
main.pack(fill="both", expand=True, padx=28, pady=(0, 20))

left = tk.Frame(main, bg=BG, width=355)
left.pack(side="left", fill="y", padx=(0, 14))
left.pack_propagate(False)

right = tk.Frame(main, bg=BG)
right.pack(side="right", fill="both", expand=True)


# Server connection card
server_card = tk.Frame(
    left, bg=CARD, highlightbackground=BORDER, highlightthickness=1
)
server_card.pack(fill="x", pady=(0, 14))

server_inner = tk.Frame(server_card, bg=CARD)
server_inner.pack(fill="x", padx=18, pady=18)

section_title(
    server_inner, "Server Connection",
    "Connect this client to the classroom NetDesk server."
)

tk.Label(
    server_inner, text="NETDESK SERVER IP",
    font=("Segoe UI", 8, "bold"), bg=CARD, fg=MUTED
).pack(anchor="w", pady=(8, 5))

server_entry = tk.Entry(
    server_inner, font=("Segoe UI", 10),
    bg="#0b1428", fg=TEXT, insertbackground=TEXT,
    relief="flat", bd=0
)
server_entry.insert(0, get_local_ip())
server_entry.pack(fill="x", ipady=9, pady=(0, 9))

modern_button(
    server_inner, "Connect to Server", connect_server,
    width=25, accent=True
).pack(fill="x")


# Network diagnostics card
network_card = tk.Frame(
    left, bg=CARD, highlightbackground=BORDER, highlightthickness=1
)
network_card.pack(fill="x", pady=(0, 14))

network_inner = tk.Frame(network_card, bg=CARD)
network_inner.pack(fill="x", padx=18, pady=18)

section_title(
    network_inner, "Network Diagnostics",
    "Test connectivity and identify common network issues."
)

tk.Label(
    network_inner, text="ROUTER / DEFAULT GATEWAY",
    font=("Segoe UI", 8, "bold"), bg=CARD, fg=MUTED
).pack(anchor="w", pady=(8, 5))

router_entry = tk.Entry(
    network_inner, font=("Segoe UI", 10),
    bg="#0b1428", fg=TEXT, insertbackground=TEXT,
    relief="flat", bd=0
)
router_entry.pack(fill="x", ipady=8, pady=(0, 9))

tk.Label(
    network_inner, text="TARGET IP / WEBSITE",
    font=("Segoe UI", 8, "bold"), bg=CARD, fg=MUTED
).pack(anchor="w", pady=(3, 5))

target_entry = tk.Entry(
    network_inner, font=("Segoe UI", 10),
    bg="#0b1428", fg=TEXT, insertbackground=TEXT,
    relief="flat", bd=0
)
target_entry.pack(fill="x", ipady=8, pady=(0, 12))

modern_button(
    network_inner, "Test Network", test_network, width=25
).pack(fill="x", pady=3)
modern_button(
    network_inner, "Diagnose Network", diagnose_network, width=25
).pack(fill="x", pady=3)
modern_button(
    network_inner, "Check Classroom Devices", check_devices, width=25
).pack(fill="x", pady=3)


# Resources card
resource_card = tk.Frame(
    left, bg=CARD, highlightbackground=BORDER, highlightthickness=1
)
resource_card.pack(fill="x")

resource_inner = tk.Frame(resource_card, bg=CARD)
resource_inner.pack(fill="x", padx=18, pady=18)

section_title(
    resource_inner, "Classroom Resources",
    "Access files shared by the NetDesk server."
)

modern_button(
    resource_inner, "View Shared Resources",
    view_resources, width=25
).pack(fill="x", pady=(2, 8))

resource_grid = tk.Frame(resource_inner, bg=CARD)
resource_grid.pack(fill="x")

tk.Label(
    resource_grid, text="Folder",
    font=("Segoe UI", 8, "bold"), bg=CARD, fg=MUTED
).grid(row=0, column=0, sticky="w", padx=(0, 6))
tk.Label(
    resource_grid, text="File",
    font=("Segoe UI", 8, "bold"), bg=CARD, fg=MUTED
).grid(row=0, column=1, sticky="w")

resource_folder_entry = tk.Entry(
    resource_grid, width=14, font=("Segoe UI", 9),
    bg="#0b1428", fg=TEXT, insertbackground=TEXT,
    relief="flat", bd=0
)
resource_folder_entry.grid(
    row=1, column=0, sticky="ew", padx=(0, 6), ipady=7
)

resource_file_entry = tk.Entry(
    resource_grid, width=22, font=("Segoe UI", 9),
    bg="#0b1428", fg=TEXT, insertbackground=TEXT,
    relief="flat", bd=0
)
resource_file_entry.grid(
    row=1, column=1, sticky="ew", ipady=7
)

resource_grid.columnconfigure(1, weight=1)

tk.Button(
    resource_inner, text="Download Resource",
    command=download_resource,
    font=("Segoe UI", 9, "bold"),
    bg=CARD_ALT, fg=TEXT,
    activebackground="#203252", activeforeground=TEXT,
    relief="flat", bd=0, cursor="hand2", pady=8
).pack(fill="x", pady=(9, 0))


# Console/output card
output_card = tk.Frame(
    right, bg=CARD, highlightbackground=BORDER, highlightthickness=1
)
output_card.pack(fill="both", expand=True)

output_header = tk.Frame(output_card, bg=CARD)
output_header.pack(fill="x", padx=18, pady=(16, 10))

tk.Label(
    output_header, text="NETDESK CONSOLE",
    font=("Segoe UI", 12, "bold"), bg=CARD, fg=TEXT
).pack(side="left")

tk.Label(
    output_header, text=" LIVE NETWORK OUTPUT",
    font=("Segoe UI", 8, "bold"), bg=CARD, fg=SUCCESS
).pack(side="left", padx=(10, 0), pady=(3, 0))

modern_button(
    output_header, "Clear", clear_result, width=8
).pack(side="right")

console_frame = tk.Frame(output_card, bg="#08111f")
console_frame.pack(fill="both", expand=True, padx=18, pady=(0, 18))

result_box = scrolledtext.ScrolledText(
    console_frame, width=78, height=30,
    font=("Consolas", 10),
    bg="#08111f", fg="#dbeafe",
    insertbackground=TEXT,
    selectbackground="#1e3a5f",
    selectforeground="#ffffff",
    relief="flat", bd=0, padx=14, pady=14
)
result_box.pack(fill="both", expand=True)

show("Welcome to NetDesk.")
show("Connect to the classroom server to begin.")
show("")


# Footer
footer = tk.Frame(window, bg=BG)
footer.pack(fill="x", padx=28, pady=(0, 12))

tk.Label(
    footer,
    text="NetDesk • LAN • TCP/IP • Client-Server • Network Monitoring",
    font=("Segoe UI", 8), bg=BG, fg=MUTED
).pack(side="left")

tk.Label(
    footer, text="v1.0",
    font=("Segoe UI", 8, "bold"), bg=BG, fg=MUTED
).pack(side="right")

window.mainloop()
