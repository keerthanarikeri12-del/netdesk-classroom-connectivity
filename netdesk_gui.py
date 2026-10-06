import tkinter as tk
from tkinter import scrolledtext, messagebox
import socket
import subprocess
import platform
import time
import csv
from datetime import datetime


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


# ---------- GUI ----------

window = tk.Tk()
window.title("NetDesk - Classroom Connectivity Assistant")
window.geometry("720x670")


tk.Label(
    window,
    text="NETDESK",
    font=("Arial", 22, "bold")
).pack(pady=10)


tk.Label(
    window,
    text="Classroom Connectivity Assistant",
    font=("Arial", 12)
).pack()


tk.Label(
    window,
    text="Router / Default Gateway IP:"
).pack(pady=(20, 5))

router_entry = tk.Entry(window, width=35)
router_entry.pack()


tk.Label(
    window,
    text="Target IP or Website:"
).pack(pady=(15, 5))

target_entry = tk.Entry(window, width=35)
target_entry.pack()


tk.Button(
    window,
    text="Test Network",
    width=25,
    command=test_network
).pack(pady=12)


tk.Button(
    window,
    text="Diagnose Network",
    width=25,
    command=diagnose_network
).pack(pady=5)


tk.Button(
    window,
    text="Check Classroom Devices",
    width=25,
    command=check_devices
).pack(pady=5)


tk.Button(
    window,
    text="View History",
    width=25,
    command=view_history
).pack(pady=5)


result_box = scrolledtext.ScrolledText(
    window,
    width=78,
    height=18
)

result_box.pack(pady=20)


window.mainloop()