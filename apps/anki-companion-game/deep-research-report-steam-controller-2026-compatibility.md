# Building a Steam Input haptics test app

The public information is enough to answer your core question: there **is** a documented way to make a tiny app vibrate Steam Input devices, and it is **not** all happening behind closed doors. The supported, developer-facing route is the **Steam Input API** inside Steamworks. Valve’s docs describe Steam Input as the layer that sits between the controller and the application, and they document both the **legacy/emulation** path and the **native API** path. On Windows, Valve says Steam Input can hook **XInput, DirectInput, RawInput, and Windows.Gaming.Input** and inject an **emulated Xbox controller**; separately, the Steam Input API exposes direct controller handles and explicit haptics calls. citeturn5view3turn1view2turn1view0

For haptics specifically, Valve’s current API docs are unusually direct. They say `TriggerRepeatedHapticPulse` is supported on **Steam Controller, Steam Deck, and Nintendo Switch Pro Controller**; they say `TriggerVibration` generates traditional rumble; and they explicitly note that **Steam Controller and Steam Deck emulate rumble using their haptics**. In other words, for a “press a button and buzz the controller” utility, Valve already documents both a **rumble-style output** path and a more **haptic-pulse-style output** path. citeturn4view0

## What Valve documents publicly

Valve’s own conceptual docs divide Steam Input into two modes. In **legacy mode**, Steam acts like a powerful mapper for games and apps that did not implement Steam Input directly. In **native mode**, the game or app talks to Steam Input through `ISteamInput`, using named actions and explicit API calls. That is already the public answer to “how do games communicate through Steam to the controller?”: either the game talks to standard APIs and Steam emulates an Xbox controller, or the game talks to Steam Input directly through the Steamworks API. citeturn5view0turn1view2

That matters because it means two separate technical strategies are available to you:

First, an app can rely on **Steam’s virtual-controller layer** and keep using ordinary XInput-like logic. That is the path most similar to how a Game Pass game behaves after being routed through Steam. Second, an app can skip the XInput middleman and call **Steam Input haptics APIs directly**, which is the cleaner route if your real goal is “buzz a Steam Controller or Steam Deck control surface on command.” Valve documents both routes, and for haptics the official docs are much clearer on the native API side. citeturn1view2turn4view0

There is also a useful subtlety in the haptics APIs themselves. Valve documents the low-level single-pulse function as effectively legacy and notes it is only for the original Valve controller, while the **repeated haptic pulse** call is documented for Steam Controller and Steam Deck. So if you want short, crisp “click” or “texture” feedback that feels more like a Steam touchpad actuator than a generic gamepad motor, the repeated-pulse API is the better first place to experiment. citeturn4view0

## Running the app without launching it from the Steam UI

Here the answer is more encouraging than it may look from the outside. Valve’s Steamworks API docs say `SteamAPI_Init` needs the **Steam client running** and a valid **App ID** context, but they also explicitly document a development workflow where you launch the executable **directly**, not from the Steam library UI, by placing a `steam_appid.txt` file next to the executable. Valve even uses **480** as the example App ID in the docs, and the Spacewar example is documented as runnable directly from Visual Studio or from the built executable as long as Steam is running in the background and the `steam_appid.txt` file is present. citeturn16view0turn16view2

So the answer to “can I make a little app that just runs and vibrates the controller without having to launch it through the Steam interface?” is **yes, during development**—with an important caveat. The **Steam client still has to be running**, because Valve says the client provides the implementations of the Steamworks interfaces. Direct launch is supported for development; “no Steam at all” is not the official path. Valve’s docs also recommend `SteamAPI_RestartAppIfNecessary` for normal shipping behavior, but they explicitly say the presence of `steam_appid.txt` suppresses that relaunch behavior for development and testing. citeturn16view0turn1view3

If you also want to test Steam Input action configurations locally, Valve documents a way to override the action manifest path with `SetInputActionManifestFilePath`, and says that override is remembered for the rest of the Steam session. That is useful because it means a locally run helper app can, in principle, be iterated on outside the Steam library UI while still using Steam Input’s native APIs. citeturn9view0

There is one nuance worth keeping in view. Valve’s support page for the original Steam Controller says the **Steam Overlay is vital to Steam Controller functionality** in normal user-facing game scenarios and advises adding non-Steam games to the Steam library when needed. That does **not** contradict the direct-launch development workflow above; it just means there are really two contexts: end-user compatibility for arbitrary applications, and developer testing of a Steamworks-enabled binary. citeturn15search1turn16view0

## The smallest supported helper app

For a vibration-only helper, the documented minimum is surprisingly small. You need the Steamworks runtime DLL next to the executable on Windows, you need `SteamAPI_Init`, you need `SteamInput()->Init()`, and you need a controller handle. Valve documents two ways to get that handle: enumerate controllers with `GetConnectedControllers`, or map an emulated gamepad slot with `GetControllerForGamepadIndex`. The latter is especially interesting for your Anki use case, because Valve documents that it maps an **XInput slot index** to a **Steam Input handle**. citeturn16view0turn2view4turn4view0

A minimal C++ skeleton would look like this:

```cpp
// Steam client must be running.
// During development, place steam_appid.txt next to the exe.

if (!SteamAPI_Init()) {
    return 1;
}

SteamInput()->Init();

InputHandle_t handles[STEAM_INPUT_MAX_COUNT] = {};
int count = SteamInput()->GetConnectedControllers(handles);

if (count > 0) {
    // Steam-style haptic pulses
    SteamInput()->TriggerRepeatedHapticPulse(
        handles[0],
        k_ESteamControllerPad_Right,
        50000,   // on: 50 ms
        50000,   // off: 50 ms
        5,       // repeat 5 times
        0
    );

    // Or generic rumble-style output
    SteamInput()->TriggerVibration(handles[0], 12000, 12000);
}

SteamInput()->Shutdown();
SteamAPI_Shutdown();
```

That outline matches the functions Valve documents: initialize Steamworks, initialize Steam Input, obtain a controller handle, then call either the **repeated haptic pulse** API or the **rumble** API. Valve’s docs describe the repeated-pulse parameters in microseconds and describe `TriggerVibration` as the traditional rumble path, with Steam Controller and Steam Deck emulating rumble through haptics. citeturn4view0turn16view0

There is a strong practical implication here for your Python/Anki setup. Because the official haptics calls are in Steamworks, the cleanest engineering pattern is probably **not** to make your Python add-on talk to Steamworks directly. The cleaner pattern is a **tiny native helper executable**—C++ if you want the shortest path from Valve’s docs, or C# if you want easier Windows tooling—and then let Anki call that helper through a subprocess, a named pipe, or localhost IPC. That is an architectural inference from Valve’s API shape, but it is a very natural one: Steamworks owns the controller handle and haptic calls, while Anki just emits “buzz now” messages. citeturn1view0turn2view4turn4view0

If you want a public reference implementation rather than starting from scratch, there is one. The public `Steamworks.NET-Test` project includes a `SteamInputTest` harness that initializes Steam Input and exposes buttons that call `TriggerVibrationExtended`, `SetLEDColor`, and the legacy haptic pulse functions. Steamworks.NET itself describes itself as a C# wrapper that stays very close to Valve’s original C++ API. That makes a small Windows helper in C# a very realistic route. citeturn28view0turn14search3

One subtle but important inference: a pure “buzz the controller” helper **probably does not need a full action manifest** if you are not consuming action-based input, because the output calls operate on `InputHandle_t` values returned by enumeration or XInput-slot mapping. Valve’s action-manifest docs are about **action sets, official configs, and bindings**, not about the output functions themselves. If later you want the same helper to also read Steam Input actions or ship polished per-device layouts, then the action-manifest path becomes relevant. citeturn8view0turn8view1turn2view4turn4view0

## Bridging an existing XInput-style app

If you do not want to redesign your app around Steamworks yet, there is a second public strategy: leave your app mostly XInput-shaped and let Steam bridge it. Valve’s Windows documentation says Steam Input can hook the traditional controller APIs and inject an **emulated Xbox controller**. Separately, Valve documents `GetControllerForGamepadIndex`, which translates an **emulated gamepad slot** into a Steam Input handle. That means an external helper can, in principle, watch the same XInput slot your app is already using and then fire haptics through Steam Input directly. citeturn1view2turn2view4

That exact “make non-Steam or incompatible apps behave like Steam-aware apps” problem is what community tools like **GloSC** and **GlosSI** were built around. GloSC describes itself as a way to use the Steam Controller as a **system-wide XInput controller** with a **system-wide Steam overlay**, and it specifically advertises **working rumble emulation**. GlosSI, the later successor, says it redirects controller input to a **virtual system-level Xbox 360 controller** and brings full Steam Input functionality to the desktop and applications that were previously incompatible. citeturn12view0turn12view1

The catch is that GlosSI also says its architecture depends heavily on **ViGEm**, and the project’s README states that ViGEm’s end-of-life effectively kills GlosSI in its current form until a successor exists. On top of that, public bug reports show that Steam Input rumble passthrough is not perfect in every stack. There are documented reports of rumble not being transmitted correctly in some Steam Input emulation scenarios, especially outside native Steam Input integrations. Those reports are not the final word on Windows, but they are a good reminder that the emulation path is more fragile than the native API path. citeturn12view1turn26search15turn26search3turn19search6

So if the real goal is **reliable app-driven haptics for a specific workflow**, the supported Steam Input helper is the stronger design. If the goal is **minimum code change** to an existing XInput app, the Steam-emulated-XInput route is still worth testing.

## What bypassing Steam entirely really means

There absolutely are public, non-Valve projects that bypass Steam. For the **original Steam Controller**, there is a small C++ library that says it can access the controller on **Windows, Linux, and macOS without Steam**, exposing button, axis, and motion data. There is also a standalone userland driver that advertises **haptic feedback** in both Xbox 360 emulation and desktop modes, and `sc-controller` advertises **haptic feedback and in-game rumble support without ever launching Steam**. This proves that the hardware protocol has been studied in public and that direct-control software exists. citeturn22view0turn22view2turn22view1

For **Steam Deck** controls on Linux, the same pattern exists. OpenSD is an open-source userspace driver that aims to use Steam Deck hardware **without Steam**, advertises force-feedback and haptics, and explicitly states that its goal is to avoid proprietary dependence on the Steam client. On the Linux kernel side, the `hid-steam` driver source openly documents that some user-space applications—**notably the Steam client**—use the **hidraw** interface directly and create input devices, which is one of the clearest public hints about how Steam itself talks to this class of hardware on Linux. citeturn20view0turn20view1

But that is reverse-engineering territory, not the official Windows developer path. Valve’s public developer docs point application authors to **Steam Input / Steamworks**, while the direct-HID ecosystem lives in community repositories and drivers. For the **2026 Steam Controller**, the public state of things is even more unsettled. SDL opened a public tracking issue listing the new controller’s **touchpads, HD haptics, gyro, back buttons, and “Grip Sense”**, and the issue explicitly raises concern that the Steam client may take **exclusive HID control**, as happens with Steam Deck, which would complicate direct outside-Steam access to advanced features. That is a strong sign that direct-HID support for the new controller is still maturing in public. citeturn5view3turn22view4turn20view1

So the realistic takeaway is this: **bypassing Steam entirely is possible for old hardware and especially on Linux, but it is the unofficial path**. On Windows, and especially for new controller hardware, that is not the route I would choose first if your goal is simply to get dependable haptics working.

## Practical conclusion for your use case

The most important result of this research is that your idea is technically sound. A little “press play and vibrate the controller” program is **not** some secret capability only large studios can use. The best-supported way to do it is a native helper app built on **Steam Input via Steamworks**. During development, Valve documents that such an app can be launched **directly** with `steam_appid.txt` next to the executable, as long as the Steam client is running in the background. If you later wanted to ship this as a real product with your own App ID, Steamworks and Steam Direct are Valve’s documented path for that. citeturn16view0turn16view2turn25search2turn25search6

For your specific Anki case, the highest-confidence architecture is: keep Anki simple, have the add-on send a tiny local command to a separate helper, and let that helper own `SteamAPI_Init`, `SteamInput()->Init`, controller enumeration, and `TriggerRepeatedHapticPulse` / `TriggerVibration`. That gives you **app-driven haptics** without requiring Anki itself to be launched from the Steam library UI every time, while still staying on Valve’s documented controller stack. If you reject Steamworks entirely, the public alternatives are GlosSI/GloSC-style virtualization or reverse-engineered controller libraries and drivers, but those are plainly the more fragile options—especially for the 2026 controller. citeturn4view0turn2view4turn12view0turn12view1turn22view4