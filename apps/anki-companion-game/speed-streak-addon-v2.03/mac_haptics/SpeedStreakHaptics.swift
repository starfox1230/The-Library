import AppKit
import CoreHaptics
import Foundation
import GameController

private let protocolVersion = 1
private let helperVersion = "2.03"

#if arch(arm64)
private let helperArchitecture = "arm64"
#elseif arch(x86_64)
private let helperArchitecture = "x86_64"
#else
private let helperArchitecture = "unknown"
#endif

private struct HapticStep: Decodable {
    let duration: Double
    let weak: Float
    let strong: Float
}

private struct HelperCommand: Decodable {
    let command: String
    let id: String?
    let steps: [HapticStep]?
}

private final class JSONEmitter {
    private let queue = DispatchQueue(label: "com.speedstreak.haptics.stdout")

    func emit(_ payload: [String: Any]) {
        queue.sync {
            guard JSONSerialization.isValidJSONObject(payload),
                  let data = try? JSONSerialization.data(withJSONObject: payload),
                  var line = String(data: data, encoding: .utf8)
            else {
                return
            }
            line.append("\n")
            FileHandle.standardOutput.write(Data(line.utf8))
        }
    }
}

private final class ControllerHaptics {
    let controller: GCController
    let localities: [String]

    private var leftEngine: CHHapticEngine?
    private var rightEngine: CHHapticEngine?
    private var defaultEngine: CHHapticEngine?
    private var players: [CHHapticPatternPlayer] = []
    private var playGeneration = UUID()

    var available: Bool {
        leftEngine != nil || rightEngine != nil || defaultEngine != nil
    }

    var activeLocalities: [String] {
        var values: [String] = []
        if leftEngine != nil {
            values.append(GCHapticsLocality.leftHandle.rawValue)
        }
        if rightEngine != nil {
            values.append(GCHapticsLocality.rightHandle.rawValue)
        }
        if defaultEngine != nil {
            values.append(GCHapticsLocality.default.rawValue)
        }
        return values.sorted()
    }

    init(controller: GCController) {
        self.controller = controller

        guard let haptics = controller.haptics else {
            localities = []
            return
        }

        let supported = haptics.supportedLocalities
        localities = supported.map(\.rawValue).sorted()
        let hasDualRumble = supported.contains(.leftHandle) && supported.contains(.rightHandle)

        if hasDualRumble {
            leftEngine = Self.makeEngine(haptics: haptics, locality: .leftHandle)
            rightEngine = Self.makeEngine(haptics: haptics, locality: .rightHandle)
        } else {
            let fallbackLocality: GCHapticsLocality?
            if supported.contains(.default) {
                fallbackLocality = .default
            } else {
                fallbackLocality = supported.first
            }
            if let fallbackLocality {
                defaultEngine = Self.makeEngine(haptics: haptics, locality: fallbackLocality)
            }
        }
    }

    func play(steps rawSteps: [HapticStep]) -> Bool {
        guard available else {
            return false
        }

        let steps = rawSteps.map {
            HapticStep(
                duration: max(0, min(10_000, $0.duration)),
                weak: max(0, min(1, $0.weak)),
                strong: max(0, min(1, $0.strong))
            )
        }
        guard !steps.isEmpty else {
            return false
        }

        stop()
        let generation = UUID()
        playGeneration = generation
        var started = false

        if let leftEngine {
            started = startPattern(engine: leftEngine, steps: steps) { $0.strong } || started
        }
        if let rightEngine {
            started = startPattern(engine: rightEngine, steps: steps) { $0.weak } || started
        }
        if let defaultEngine {
            started = startPattern(engine: defaultEngine, steps: steps) {
                min(1, $0.strong + $0.weak)
            } || started
        }

        let totalSeconds = steps.reduce(0.0) { $0 + ($1.duration / 1_000.0) }
        DispatchQueue.main.asyncAfter(deadline: .now() + totalSeconds + 0.1) { [weak self] in
            guard let self, self.playGeneration == generation else {
                return
            }
            self.players.removeAll()
        }
        return started
    }

    func stop() {
        playGeneration = UUID()
        for player in players {
            try? player.stop(atTime: CHHapticTimeImmediate)
        }
        players.removeAll()
    }

    func shutdown() {
        stop()
        for engine in [leftEngine, rightEngine, defaultEngine] {
            engine?.stop(completionHandler: nil)
        }
    }

    private func startPattern(
        engine: CHHapticEngine,
        steps: [HapticStep],
        intensity: (HapticStep) -> Float
    ) -> Bool {
        var relativeTime = 0.0
        var events: [CHHapticEvent] = []

        for step in steps {
            let seconds = step.duration / 1_000.0
            let magnitude = max(0, min(1, intensity(step)))
            if seconds > 0, magnitude > 0 {
                let parameters = [
                    CHHapticEventParameter(parameterID: .hapticIntensity, value: magnitude),
                    CHHapticEventParameter(parameterID: .hapticSharpness, value: 1.0),
                ]
                events.append(
                    CHHapticEvent(
                        eventType: .hapticContinuous,
                        parameters: parameters,
                        relativeTime: relativeTime,
                        duration: seconds
                    )
                )
            }
            relativeTime += seconds
        }

        guard !events.isEmpty else {
            return true
        }

        do {
            try engine.start()
            let pattern = try CHHapticPattern(events: events, parameters: [])
            let player = try engine.makePlayer(with: pattern)
            try player.start(atTime: CHHapticTimeImmediate)
            players.append(player)
            return true
        } catch {
            return false
        }
    }

    private static func makeEngine(
        haptics: GCDeviceHaptics,
        locality: GCHapticsLocality
    ) -> CHHapticEngine? {
        guard let engine = haptics.createEngine(withLocality: locality) else {
            return nil
        }
        engine.playsHapticsOnly = true
        engine.isAutoShutdownEnabled = false
        engine.stoppedHandler = { [weak engine] reason in
            guard reason != .gameControllerDisconnect else {
                return
            }
            try? engine?.start()
        }
        engine.resetHandler = { [weak engine] in
            try? engine?.start()
        }
        return engine
    }
}

private final class HapticsManager {
    private let emitter: JSONEmitter
    private var sessions: [ObjectIdentifier: ControllerHaptics] = [:]
    private var observers: [NSObjectProtocol] = []
    private(set) var backgroundMonitoringEnabled = false

    init(emitter: JSONEmitter) {
        self.emitter = emitter

        if #available(macOS 11.3, *) {
            GCController.shouldMonitorBackgroundEvents = true
            backgroundMonitoringEnabled = true
        }

        observers.append(
            NotificationCenter.default.addObserver(
                forName: .GCControllerDidConnect,
                object: nil,
                queue: .main
            ) { [weak self] notification in
                guard let controller = notification.object as? GCController else {
                    return
                }
                self?.attach(controller)
                self?.emitStatus(reason: "connected")
            }
        )
        observers.append(
            NotificationCenter.default.addObserver(
                forName: .GCControllerDidDisconnect,
                object: nil,
                queue: .main
            ) { [weak self] notification in
                guard let controller = notification.object as? GCController else {
                    return
                }
                self?.detach(controller)
                self?.emitStatus(reason: "disconnected")
            }
        )

        for controller in GCController.controllers() {
            attach(controller)
        }
        GCController.startWirelessControllerDiscovery(completionHandler: nil)
    }

    deinit {
        for observer in observers {
            NotificationCenter.default.removeObserver(observer)
        }
        shutdown()
    }

    func handle(_ command: HelperCommand) {
        switch command.command {
        case "status":
            emitStatus(reason: "requested", requestID: command.id)
        case "play":
            let played = play(steps: command.steps ?? [])
            emitter.emit([
                "event": "playResult",
                "id": command.id ?? "",
                "accepted": played,
                "hapticControllerCount": hapticSessionCount,
            ])
        case "stop":
            stop()
            emitter.emit(["event": "stopped", "id": command.id ?? ""])
        case "shutdown":
            shutdown()
            emitter.emit(["event": "shutdown", "id": command.id ?? ""])
            NSApplication.shared.terminate(nil)
        default:
            emitter.emit([
                "event": "error",
                "id": command.id ?? "",
                "code": "unknown_command",
                "message": "Unsupported command: \(command.command)",
            ])
        }
    }

    func emitStatus(reason: String, requestID: String? = nil) {
        let controllerPayloads: [[String: Any]] = sessions.values.map { session in
            [
                "vendorName": session.controller.vendorName ?? "Unknown controller",
                "productCategory": session.controller.productCategory,
                "hapticsAvailable": session.available,
                "supportedLocalities": session.localities,
                "activeLocalities": session.activeLocalities,
                "engineCreationFailed": !session.localities.isEmpty && !session.available,
            ]
        }
        emitter.emit([
            "event": "status",
            "id": requestID ?? "",
            "reason": reason,
            "backend": "native-macos-gamecontroller",
            "controllerCount": sessions.count,
            "hapticControllerCount": hapticSessionCount,
            "backgroundMonitoringEnabled": backgroundMonitoringEnabled,
            "controllers": controllerPayloads,
        ])
    }

    func shutdown() {
        GCController.stopWirelessControllerDiscovery()
        for session in sessions.values {
            session.shutdown()
        }
        sessions.removeAll()
    }

    private var hapticSessionCount: Int {
        sessions.values.filter(\.available).count
    }

    private func attach(_ controller: GCController) {
        let identifier = ObjectIdentifier(controller)
        guard sessions[identifier] == nil else {
            return
        }
        sessions[identifier] = ControllerHaptics(controller: controller)
    }

    private func detach(_ controller: GCController) {
        let identifier = ObjectIdentifier(controller)
        sessions.removeValue(forKey: identifier)?.shutdown()
    }

    private func play(steps: [HapticStep]) -> Bool {
        var played = false
        for session in sessions.values where session.available {
            played = session.play(steps: steps) || played
        }
        return played
    }

    private func stop() {
        for session in sessions.values {
            session.stop()
        }
    }
}

private let emitter = JSONEmitter()
private let application = NSApplication.shared
application.setActivationPolicy(.accessory)
private let manager = HapticsManager(emitter: emitter)

emitter.emit([
    "event": "ready",
    "protocolVersion": protocolVersion,
    "helperVersion": helperVersion,
    "backend": "native-macos-gamecontroller",
    "architecture": helperArchitecture,
    "macOSVersion": ProcessInfo.processInfo.operatingSystemVersionString,
    "processIdentifier": Int(ProcessInfo.processInfo.processIdentifier),
    "frameworksInitialized": ["GameController", "CoreHaptics"],
    "backgroundMonitoringEnabled": manager.backgroundMonitoringEnabled,
])
manager.emitStatus(reason: "startup")

DispatchQueue.global(qos: .userInitiated).async {
    let decoder = JSONDecoder()
    while let line = readLine() {
        guard let data = line.data(using: .utf8) else {
            continue
        }
        do {
            let command = try decoder.decode(HelperCommand.self, from: data)
            DispatchQueue.main.async {
                manager.handle(command)
            }
        } catch {
            emitter.emit([
                "event": "error",
                "code": "invalid_json",
                "message": error.localizedDescription,
            ])
        }
    }
    DispatchQueue.main.async {
        manager.shutdown()
        application.terminate(nil)
    }
}

application.run()
