import boto3

gamelift = boto3.client('gamelift', 'ap-northeast-2')
response = gamelift.list_fleets()
fleet_ids = response["FleetIds"]

checked_builds = set()
shipping_latest_ids = []
shipping_latest_version = 0
development_latest_ids = []
development_latest_version = 0

response = gamelift.describe_fleet_attributes(FleetIds=fleet_ids, Limit=100)
for attr in response["FleetAttributes"]:
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

performed = False
for attr in response["FleetAttributes"]:
    if attr["BuildId"] in shipping_latest_ids or attr["BuildId"] in development_latest_ids:
        continue
    
    performed = True
    print("Delete fleet", attr['FleetId'], attr["Name"])
    #response = gamelift.delete_fleet(FleetId=attr['FleetId'])
    if response['ResponseMetadata']['HTTPStatusCode'] == 200:
        print("OK")
    else:
        print("Failed.", response)

if not performed:
    print("There is nothing to clear.")
