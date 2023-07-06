import boto3
import tkinter as tk
from tkinter import messagebox

gamelift = boto3.client('gamelift', 'ap-northeast-2')

def arry_split(arr, size):
    arrs = []
    while len(arr) > size:
        pice = arr[:size]
        arrs.append(pice)
        arr   = arr[size:]
    arrs.append(arr)
    return arrs

def delete_fleet(fleet_id):
    gamelift.delete_fleet(FleetId=fleet_id)
    messagebox.showinfo("Success", f"Fleet {fleet_id} has been deleted.")


def display_fleets(fleets):
    root = tk.Tk()
    root.title("Fleet Management")

    listbox = tk.Listbox(root, selectmode=tk.EXTENDED, width=80)
    listbox.pack()

    for fleet in fleets:
        listbox.insert(tk.END, fleet['Name'])

    def select_all():
        listbox.selection_set(0, tk.END)

    def delete_selected():
        selected_indices = listbox.curselection()
        if not selected_indices:
            messagebox.showwarning("Warning", "No fleets selected.")
            return

        confirmed = messagebox.askyesno("Confirmation", "Are you sure you want to delete the selected fleets?")
        if not confirmed:
            return

        selected_fleets = [fleets[i] for i in selected_indices]

        delete_results = []
        for fleet in selected_fleets:
            result = delete_fleet(fleet['FleetId'])
            delete_results.append(result)

        # Show delete results in a single message box
        messagebox.showinfo("Deletion Results", "\n".join(delete_results))

        # Close the UI
        root.destroy()

    select_all_button = tk.Button(root, text="Select All", command=select_all)
    select_all_button.pack()

    delete_button = tk.Button(root, text="Delete Selected", command=delete_selected)
    delete_button.pack()

    root.mainloop()

def get_all_fleet_attributes():
    fleet_ids = []

    checked_builds = set()
    shipping_latest_ids = []
    shipping_latest_version = 0
    development_latest_ids = []
    development_latest_version = 0

    # Get fleet IDs
    response = gamelift.list_fleets()
    fleet_ids.extend(response["FleetIds"])

    while "NextToken" in response:
        response = gamelift.list_fleets(NextToken=response["NextToken"])
        fleet_ids.extend(response["FleetIds"])

    fleets_to_delete = []

    # Get fleet attributes
    arrayids=arry_split(fleet_ids, 16)
    fleetattributes = []

    for ids in arrayids:
        response = gamelift.describe_fleet_attributes(FleetIds=ids, Limit=100)
        for tempattr in response["FleetAttributes"]:
            fleetattributes.append(tempattr)

    for attr in fleetattributes: 
        build_id = attr['BuildId']
        if build_id in checked_builds:
            continue

        checked_builds.add(build_id)
        build_response = gamelift.describe_build(BuildId=build_id)['Build']
        name = build_response['Name']
        version = int(build_response['Version'])

        if 'demo' in name:
            if shipping_latest_version < version:
                shipping_latest_version = version
                shipping_latest_ids = [build_id]
            elif shipping_latest_version == version:
                shipping_latest_ids.append(build_id)
        elif 'dev' in name:
            if development_latest_version < version:
                development_latest_version = version
                development_latest_ids = [build_id]
            elif development_latest_version == version:
                development_latest_ids.append(build_id)


    fleettoexcept= []
    for attr in fleetattributes:
        fleets_to_delete.append(attr)  # 모든 fleet 추가

    for fleet in fleets_to_delete:
        if fleet["BuildId"] in shipping_latest_ids or fleet["BuildId"] in development_latest_ids:
            fleettoexcept.append(fleet)

    for fleet in fleettoexcept:
        fleets_to_delete.remove(fleet)


    return fleets_to_delete

def main():
    fleets_to_delete = get_all_fleet_attributes()

    if not fleets_to_delete:
        print("There is nothing to clear.")
    else:
        display_fleets(fleets_to_delete)

if __name__ == "__main__":
    main()
