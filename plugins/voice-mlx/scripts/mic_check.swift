/// mic_check — Exits 0 if any audio input device is actively capturing, 1 otherwise.
///
/// Uses CoreAudio's kAudioDevicePropertyDeviceIsRunningSomewhere, which is
/// the same signal that drives the orange dot in the macOS menu bar.
///
/// Build:  swiftc mic_check.swift -framework CoreAudio -o mic_check
/// Usage:  ./mic_check && echo "mic in use" || echo "mic idle"

import CoreAudio

func isMicInUse() -> Bool {
    var propertyAddress = AudioObjectPropertyAddress(
        mSelector: kAudioHardwarePropertyDevices,
        mScope: kAudioObjectPropertyScopeGlobal,
        mElement: kAudioObjectPropertyElementMain
    )

    var dataSize: UInt32 = 0
    var status = AudioObjectGetPropertyDataSize(
        AudioObjectID(kAudioObjectSystemObject),
        &propertyAddress, 0, nil, &dataSize
    )
    guard status == noErr, dataSize > 0 else { return false }

    let deviceCount = Int(dataSize) / MemoryLayout<AudioDeviceID>.size
    var deviceIDs = [AudioDeviceID](repeating: 0, count: deviceCount)
    status = AudioObjectGetPropertyData(
        AudioObjectID(kAudioObjectSystemObject),
        &propertyAddress, 0, nil, &dataSize, &deviceIDs
    )
    guard status == noErr else { return false }

    for deviceID in deviceIDs {
        // Check if this device has input channels (i.e. is a microphone)
        var inputAddress = AudioObjectPropertyAddress(
            mSelector: kAudioDevicePropertyStreamConfiguration,
            mScope: kAudioObjectPropertyScopeInput,
            mElement: kAudioObjectPropertyElementMain
        )
        var inputSize: UInt32 = 0
        AudioObjectGetPropertyDataSize(deviceID, &inputAddress, 0, nil, &inputSize)
        guard inputSize > 0 else { continue }

        let bufferListPtr = UnsafeMutableRawPointer.allocate(
            byteCount: Int(inputSize),
            alignment: MemoryLayout<AudioBufferList>.alignment
        )
        defer { bufferListPtr.deallocate() }
        AudioObjectGetPropertyData(deviceID, &inputAddress, 0, nil, &inputSize, bufferListPtr)
        let bufferList = bufferListPtr.bindMemory(to: AudioBufferList.self, capacity: 1).pointee
        guard bufferList.mBuffers.mNumberChannels > 0 else { continue }

        // Check if any process on the system is using this input device
        var runningAddress = AudioObjectPropertyAddress(
            mSelector: kAudioDevicePropertyDeviceIsRunningSomewhere,
            mScope: kAudioObjectPropertyScopeGlobal,
            mElement: kAudioObjectPropertyElementMain
        )
        var isRunning: UInt32 = 0
        var runningSize = UInt32(MemoryLayout<UInt32>.size)
        let result = AudioObjectGetPropertyData(
            deviceID, &runningAddress, 0, nil, &runningSize, &isRunning
        )
        if result == noErr && isRunning != 0 {
            return true
        }
    }

    return false
}

let active = isMicInUse()
exit(active ? 0 : 1)
