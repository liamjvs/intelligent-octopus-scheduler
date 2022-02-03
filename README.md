# Intelligent Octopus Scheduler
Quick Python script to query using GraphQL your slots for [Intelligent Octopus](https://octopus.energy/intelligent-octopus/). I use this with Home Assistant to run my automations.

I haven't explained the logic well in the script but I wanted to prevent my automations from triggering on/off through the day. The script checks if there is a slot adjacent to it and if the slot is in the off-peak period. There are most likely some edge usecases where the script won't output the correct times - in my limited testing (and simluating different use cases) it has been working.

## io.py
You'll need to enter the two variables before executing the script:
- [Octopus Developer API Key](https://octopus.energy/dashboard/developer/)
- Octopus Account Number (found on your account section)

## Home Assistant
Add the code below to your config to call the python script. 

```yaml
sensor:
  - platform: command_line
    name: Intelligent Octopus Times
    json_attributes:
      - nextRunStart
      - nextRunEnd
      - timesObj
    command: "python3 /config/io.py"
    scan_interval: 3600
    value_template: "{{ value_json.updatedAt }}"

template:
  - binary_sensor:
    - name: "Octopus Intelligent Slot"
      state: '{{ as_timestamp(states("sensor.intelligent_octopus_start")) <= as_timestamp(now()) <= as_timestamp(states("sensor.intelligent_octopus_end")) }}'
  - sensor:
    - name: 'Intelligent Octopus Start'
      state: '{{ state_attr("sensor.intelligent_octopus_times","nextRunStart") }}'
    - name: 'Intelligent Octopus End'
      state: '{{ state_attr("sensor.intelligent_octopus_times","nextRunEnd") }}'
```

In your automations, you can use `binary_sensor.octopus_intelligent_slot`.