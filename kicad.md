## 1. Operations grounded in your actual schematic

**1. Find and focus on a component**

User: "Locate J106, the USB connector."

Agent: Finds J106 in the upper-right section and navigates the viewer to it.

Other useful targets: J101 (I²C), J102 (SWD), J108 (UART), J107 (MAX31865 extension).

Requires a component-position map and viewport navigation, not just Gemini.

**2. Explain a component's purpose**

User: "What does C101 do?"

Agent: "C101 is a 4.7 nF capacitor connected between USB_SHIELD and ground, with R101 providing a parallel high-resistance path."

The agent can explain why this network may be used for USB shield coupling, without claiming a verified design intent.

Other examples: "What's the purpose of R101?" and "What is TP103 used for?"

**3. Trace a signal connection**

User: "Where do USB D+ and D− go?"

Agent: Identifies `USB_P` and `USB_N` leaving J106 and connecting to the SAMD21 hierarchical sheet through `USB_DP` and `USB_DM`.

Another strong command: "Trace the I²C connections."

Agent: Shows SCL and SDA from J101 to the SAMD21 sheet.

For reliable electrical tracing, parse KiCad connectivity/netlist information.

4**. Navigate hierarchical schematic sheets**

User: "Open the 3.3-volt regulator."

Agent: Opens the `2_5Vto3.3VRegulator` sheet.

User: "Go to the SAMD21."

Agent: Opens the `3_uC_SAMD21` sheet.

User: "Return to the main schematic."

Agent: Navigates back to `Embedded_v1.kicad_sch`.

This is an especially convincing demonstration of task-aware navigation.

**5. Assembly checklist and progress tracking**

User: "I'm assembling the USB section."

Agent: Displays a checklist for J106, C101, R101, and relevant test points.

User: "Mark C101 complete."

Agent: Updates the checklist and suggests the next component to inspect.

A suggested assembly sequence should be reviewed against the actual BOM and manufacturing process.

**6. Guided troubleshooting**

User: "My board isn't communicating over USB."

Agent: Guides the technician through checking J106 connections, USB_P/USB_N continuity, the 3.3 V supply, and the SAMD21's USB configuration.

User: "Show me the USB section."

Agent: Navigates directly to the relevant part of the schematic.

The agent should suggest checks rather than assert a fault diagnosis without measurements.