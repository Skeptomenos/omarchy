#!/bin/bash

set -euo pipefail

source "$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)/base-test.sh"

run_node_test <<'JS'
const fs = require('fs')
const network = requireFromRoot('shell/plugins/panels/network/Model.js')
const panelSource = fs.readFileSync(root + '/shell/plugins/panels/network/Panel.qml', 'utf8')

assert(/IpcHandler[\s\S]*?function toggleNetwork\(\) \{ root\.toggleNetwork\(\) \}/.test(panelSource), 'network exposes the Wi-Fi radio toggle over IPC')
assert(/manageIpc: false/.test(panelSource), 'network owns its IPC handler so it can extend the target methods')

// Opening from the bar must call open() and nothing else. open() runs
// refresh(true), which defers the PHY scan; a second bare refresh() defaults
// scanWifi to false, sets scannerEnabled synchronously, and stalls the open on
// NetworkManager's access-point flood.
const barPress = panelSource.match(/onPressed: function\(b\) \{[\s\S]*?\n {4}\}/)
assert(barPress, 'network bar button has an onPressed handler')
const barPressCode = barPress[0].replace(/\/\/.*$/gm, '')
assert(!/refresh\(/.test(barPressCode), 'network bar click opens the panel without a second refresh that would undo the deferred scan')

// A closed panel has no nearby-network list to fill. Quickshell's scanner
// re-arms RequestScan on its own timer, and every sweep takes the radio off
// the operating channel, so a scanner left enabled behind a closed panel keeps
// degrading the connection it is scanning from.
const refreshFn = panelSource.match(/function refresh\(scanWifi\)[\s\S]*?\n {2}\}/)
assert(refreshFn, 'network has a refresh() function')
assert(/if \(opened && wifiDevice\)/.test(refreshFn[0]), 'network only touches the scanner from refresh() while its panel is open')

// The 100ms deferral can outlive the panel: closing inside the window would
// otherwise re-enable scanning from a timer nobody is watching.
const scanRestart = panelSource.match(/id: scanRestart[\s\S]*?onTriggered: \{[\s\S]*?\n {4}\}/)
assert(scanRestart, 'network has the deferred scan restart timer')
assert(/root\.opened/.test(scanRestart[0]), 'network re-checks the panel before the deferred restart re-enables scanning')
assert(/scanRestart\.stop\(\)/.test(panelSource), 'network cancels a pending scan restart when the panel closes')

// scannerEnabled lives on a shared WifiDevice with no reference counting, so
// the panel has to own what it enabled. Run the helper's own JavaScript against
// stand-in devices: the two invariants it carries are that a closed panel never
// takes a device, and that adopting a new one releases the previous.
const scannerHelper = panelSource.match(/function setScannerEnabled\(enabled\) \{[\s\S]*?\n {2}\}/)
assert(scannerHelper, 'network has a scanner ownership helper')

var opened = false
var wifiDevice = { scannerEnabled: false }
var scannerDevice = null
eval(scannerHelper[0])

setScannerEnabled(true)
assert(
  scannerDevice === null && wifiDevice.scannerEnabled === false,
  'network does not let a closed panel claim or enable a scanner device'
)

var previousScannerDevice = { scannerEnabled: true }
var replacementScannerDevice = { scannerEnabled: false }
opened = true
scannerDevice = previousScannerDevice
wifiDevice = replacementScannerDevice
setScannerEnabled(true)
assert(
  previousScannerDevice.scannerEnabled === false &&
    scannerDevice === replacementScannerDevice &&
    replacementScannerDevice.scannerEnabled === true,
  'network releases the previous scanner device before enabling its replacement'
)

// Destruction is the case a guard-only fix misses: the widget dies with the
// panel still open, as a bar reload does, and nothing else would release it.
assert(
  /Component\.onDestruction[\s\S]{0,140}scannerDevice\.scannerEnabled = false/.test(panelSource),
  'network releases the scanner it owns when the widget is destroyed'
)
assert(!/wifiDevice\.scannerEnabled\s*=/.test(panelSource), 'network writes scanner state through its owned device reference rather than the moving wifiDevice reference')

// A row is a primitive snapshot that can outlive its WifiNetwork, and
// disconnect() falls back to the live connection when handed null, so row
// activation must go through the guarded disconnectRow().
assert(
  /function disconnectRow\(ssid\) \{\s*var network = networkForSsid\(ssid\)\s*if \(network\) disconnect\(network\)/.test(panelSource),
  'network guards row disconnects so a stale row cannot drop an unrelated connection'
)
assert(!/disconnect\(\s*(root\.)?networkForSsid\(/.test(panelSource), 'network never passes an unguarded networkForSsid() lookup to disconnect()')

assertDeepEqual(
  network.parseNetworkStatus('wifi\tCafe WiFi\t78\t5200\n'),
  { kind: 'wifi', label: 'Cafe WiFi', signalStrength: 78, frequency: '5200' },
  'network parses bar status'
)
assertEqual(network.connectionIcon('wifi', 80), network.wifiIconFor(80), 'network maps wifi icon from signal')
assertEqual(network.formatHeaderSpeed('1000'), '1gbit', 'network formats gigabit speed')
assertEqual(network.formatHeaderSpeed('2500'), '2.5gbit', 'network formats fractional gigabit speed')
assertEqual(network.formatHeaderFreq('2462'), '2.4ghz', 'network formats 2.4GHz wifi band')
assertEqual(network.formatHeaderFreq('5200'), '5ghz', 'network formats 5GHz wifi band')
assertEqual(network.formatHeaderFreq('6455.0'), '6ghz', 'network formats 6GHz wifi band')
assertEqual(network.formatHeaderFreq('18300'), '18.3ghz', 'network falls back to exact GHz for unknown bands')
assertEqual(network.headerDetail({ type: 'ethernet', speed: '100' }), '100mbit', 'network header uses ethernet speed')

assertDeepEqual(
  network.parseKeyValue('iface\twlan0\nrx_bytes\t100\ntx_bytes\t50\n'),
  { iface: 'wlan0', rx_bytes: '100', tx_bytes: '50' },
  'network parses detail key values'
)
assertEqual(network.decodeIwSsid('Cafe\\xe2\\x80\\x99'), 'Cafe’', 'network decodes UTF-8 SSID bytes')
assertEqual(network.decodeIwSsid('Smile \\xf0\\x9f\\x98\\x80'), 'Smile 😀', 'network decodes emoji SSID bytes')
assertEqual(network.decodeIwSsid('\\x20Cafe\\x20'), ' Cafe ', 'network preserves edge spaces in SSIDs')
assertEqual(network.decodeIwSsid('slash\\x5cname'), 'slash\\name', 'network decodes SSID backslashes once')
assertEqual(network.decodeIwSsid('invalid\\xff'), 'invalid\\xff', 'network preserves invalid UTF-8 escapes')
assertEqual(network.decodeIwSsid('already 😀'), 'already 😀', 'network safely preserves unexpected non-BMP input')
assertDeepEqual(
  network.parseKeyValue('ssid\tline\\x0abreak\\x09tab\\x00nul\nsignal_dbm\t-40\n'),
  { ssid: 'line\\x0abreak\\x09tab\\x00nul', signal_dbm: '-40' },
  'network leaves control-byte escapes safe for single-line display'
)
assertDeepEqual(
  network.throughputState({ prevIface: '', prevSampleTime: 0 }, { iface: 'wlan0', rx_bytes: '100', tx_bytes: '50' }, 10),
  { prevIface: 'wlan0', prevRxBytes: 100, prevTxBytes: 50, prevSampleTime: 10, downloadRate: 0, uploadRate: 0 },
  'network seeds throughput state on first sample'
)
assertDeepEqual(
  network.throughputState({ prevIface: 'wlan0', prevRxBytes: 100, prevTxBytes: 50, prevSampleTime: 10 }, { iface: 'wlan0', rx_bytes: '300', tx_bytes: '90' }, 12),
  { prevIface: 'wlan0', prevRxBytes: 300, prevTxBytes: 90, prevSampleTime: 12, downloadRate: 100, uploadRate: 20 },
  'network computes throughput deltas'
)

let ping = network.pingLatencyState(
  { pingIface: '', routerPingSamples: [], internetPingSamples: [] },
  { iface: 'wlan0', router_ping_ms: '2.0', internet_ping_ms: '20.0' },
  4
)
assertDeepEqual(
  ping,
  { pingIface: 'wlan0', routerPingSamples: [2], internetPingSamples: [20], routerPingLatency: 2, internetPingLatency: 20, internetPingPacketLoss: 0 },
  'network seeds ping latency samples'
)

ping = network.pingLatencyState(ping, { iface: 'wlan0', router_ping_ms: '4.0', internet_ping_ms: '' }, 4)
assertDeepEqual(
  ping,
  { pingIface: 'wlan0', routerPingSamples: [2, 4], internetPingSamples: [20, null], routerPingLatency: 3, internetPingLatency: 20, internetPingPacketLoss: 50 },
  'network averages recent successful ping samples'
)

assertDeepEqual(
  network.pingLatencyState(ping, { iface: 'eth0', router_ping_ms: '1.5', internet_ping_ms: '10.0' }, 4),
  { pingIface: 'eth0', routerPingSamples: [1.5], internetPingSamples: [10], routerPingLatency: 1.5, internetPingLatency: 10, internetPingPacketLoss: 0 },
  'network resets ping samples when interface changes'
)

assertDeepEqual(
  network.pingLatencyState(ping, { iface: 'wlan0', internet_ping_ms: '22.0' }, 4),
  { pingIface: 'wlan0', routerPingSamples: [], internetPingSamples: [20, null, 22], routerPingLatency: -1, internetPingLatency: 21, internetPingPacketLoss: 33 },
  'network clears ping samples when a target is unavailable'
)

assertEqual(network.formatBytes(1536), '1.5 KB', 'network formats bytes')
assertEqual(network.formatRate(1536), '1.5 KB/s', 'network formats rates')
assertEqual(network.formatPingLatency('2.54'), '2.5 ms', 'network formats low ping with precision')
assertEqual(network.formatPingLatency('25.4'), '25 ms', 'network formats ping')
assertEqual(network.formatPingLatency(''), 'Timeout', 'network formats missing ping as timeout')
assertEqual(network.formatPingLatency(-1, false), '--', 'network holds the ping row before the first sample')
assertEqual(network.formatPingLatency('25.4', true), '25 ms', 'network formats ping once samples exist')
assertEqual(network.formatPingLatency('', true), 'Timeout', 'network still reports a timeout among real samples')
assertEqual(network.formatPacketLoss(2), '2%', 'network formats packet loss')
assertEqual(network.formatPacketLoss(0), '0%', 'network formats zero packet loss')
assertEqual(network.formatPacketLoss(0, false), '--', 'network holds the packet loss row before the first sample')
assertEqual(network.formatPacketLoss(0, true), '0%', 'network reports zero loss once samples exist')

const rows = network.sortWifiRows([
  { ssid: 'Open', connected: false, known: false, signal: 95 },
  { ssid: 'Known', connected: false, known: true, signal: 10 },
  { ssid: 'Connected', connected: true, known: true, signal: 20 }
])
assertDeepEqual(rows.map(row => row.ssid), ['Connected', 'Known', 'Open'], 'network sorts wifi rows by connection and known state')
assertEqual(network.wifiSectionTitle(rows, 0), 'KNOWN NETWORKS', 'network labels known wifi section')
assertEqual(network.wifiSectionTitle(rows, 2), 'OTHER NETWORKS', 'network labels other wifi section')

const wifiRow = network.wifiRow({
  connected: true,
  known: true,
  name: 'Home',
  signalStrength: 0.8,
  security: 1,
  nmSettings: [{ uuid: 'uuid-home' }, { uuid: '' }, null, { uuid: 'uuid-backup' }]
})
assertDeepEqual(
  wifiRow,
  { connected: true, known: true, ssid: 'Home', signal: 80, security: 1, profileUuids: ['uuid-home', 'uuid-backup'] },
  'network snapshots only primitive profile UUIDs with each wifi row'
)
assertDeepEqual(
  Object.keys(wifiRow).sort(),
  ['connected', 'known', 'profileUuids', 'security', 'signal', 'ssid'],
  'network wifi rows project exactly the primitive fields, so each delegate stores no live QObject'
)
assert(
  wifiRow.profileUuids.every(uuid => typeof uuid === 'string'),
  'network wifi row profile snapshots never retain NMSettings QObject wrappers'
)

const security = {
  Wpa3SuiteB192: 0,
  Sae: 1,
  Wpa2Eap: 2,
  Wpa2Psk: 3,
  WpaEap: 4,
  WpaPsk: 5,
  StaticWep: 6,
  DynamicWep: 7,
  Leap: 8,
  Owe: 9,
  Open: 10,
  Unknown: 11
}
for (const name of ['Wpa3SuiteB192', 'Sae', 'Wpa2Eap', 'Wpa2Psk', 'WpaEap', 'WpaPsk', 'StaticWep', 'DynamicWep', 'Leap', 'Unknown']) {
  assertEqual(network.requiresCredentials(security[name], security.Open, security.Owe), true, 'network asks for ' + name + ' credentials')
}
assertEqual(network.requiresCredentials(security.Owe, security.Open, security.Owe), false, 'network does not ask for OWE credentials')
assertEqual(network.requiresCredentials(security.Open, security.Open, security.Owe), false, 'network does not ask for open-network credentials')

assert(
  /Model\.requiresCredentials\(security, WifiSecurityType\.Open, WifiSecurityType\.Owe\)/.test(panelSource),
  'network wires the Quickshell OWE enum into credential detection'
)
assert(
  /if \(requiresCredentials\(net\.security\) && !net\.known\)/.test(panelSource),
  'network keyboard activation gates unknown-network prompts on credential requirements'
)
assert(
  /if \(row\.requiresCredentials && !row\.isKnown\)/.test(panelSource),
  'network row clicks gate unknown-network prompts on credential requirements'
)
assert(
  /shouldRepromptPassphrase\(reason, row\.requiresCredentials\)/.test(panelSource),
  'network failure reprompts use the row credential requirement'
)
assert(
  /networkFailureReason\(reason, requiresCredentials\(network\.security\)\)/.test(panelSource),
  'network failure copy uses the live network credential requirement'
)
assert(
  /readonly property bool canForget: root\.canForgetNetwork\(net\)/.test(panelSource),
  'network rows derive forget eligibility from the tested model helper'
)
const rightAction = panelSource.match(/Row \{\s*id: rightAction\b[\s\S]*?\n {6}\}/)
assert(rightAction, 'network has a right-edge action row')
assert(
  /visible: row\.isKnown \|\| row\.requiresCredentials/.test(rightAction[0]),
  'network keeps auto-connect and forget controls for known networks'
)
const lockIndicator = panelSource.match(/Text \{\s*id: lockIndicator\b[\s\S]*?\n {8}\}/)
assert(lockIndicator, 'network has a lock/forget indicator')
assert(
  /visible: row\.requiresCredentials \|\| row\.forgetVisible/.test(lockIndicator[0]),
  'network hides the lock on passwordless networks until showing their forget action'
)
assert(
  /forgetVisible: canForget && \(!requiresCredentials \|\| forgetFocused \|\| rightMouse\.containsMouse\)/.test(panelSource),
  'network shows the forget action directly for known passwordless networks'
)

const reasons = { NoSecrets: 1, WifiAuthTimeout: 2, WifiNetworkLost: 3, WifiClientDisconnected: 4, WifiClientFailed: 5 }
assertEqual(network.networkFailureReason(reasons.NoSecrets, true, reasons), 'Passphrase required', 'network maps missing credential failures')
assertEqual(network.networkFailureReason(reasons.WifiAuthTimeout, true, reasons), 'Wrong password', 'network maps credentialed auth timeouts')
assertEqual(network.networkFailureReason(reasons.NoSecrets, false, reasons), 'Failed to connect', 'network gives passwordless missing-secret failures generic copy')
assertEqual(network.networkFailureReason(reasons.WifiAuthTimeout, false, reasons), 'Failed to connect', 'network gives passwordless auth timeouts generic copy')
assertEqual(network.networkFailureReason(99, true, reasons), 'Failed to connect', 'network maps unknown failures')

assertEqual(network.canForgetNetwork({ known: true, connected: false, security: security.Owe }), true, 'network can forget known disconnected OWE networks')
assertEqual(network.canForgetNetwork({ known: true, connected: false, security: security.Open }), true, 'network can forget known disconnected open networks')
assertEqual(network.canForgetNetwork({ known: false, connected: false, security: security.Owe }), false, 'network cannot forget unknown networks')
assertEqual(network.canForgetNetwork({ known: true, connected: true, security: security.Owe }), false, 'network cannot forget the connected network')

assertEqual(network.shouldRepromptPassphrase(reasons.NoSecrets, true, reasons), true, 'network reprompts when required credentials are missing')
assertEqual(network.shouldRepromptPassphrase(reasons.NoSecrets, false, reasons), false, 'network does not ask a passwordless network for missing secrets')
assertEqual(network.shouldRepromptPassphrase(reasons.WifiAuthTimeout, true, reasons), true, 'network reprompts a credentialed network after a wrong password')
assertEqual(network.shouldRepromptPassphrase(reasons.WifiAuthTimeout, false, reasons), false, 'network does not reprompt an open network on auth timeout')
assertEqual(network.shouldRepromptPassphrase(reasons.WifiClientFailed, true, reasons), false, 'network does not reprompt on generic connection failures')


assertEqual(network.bandLabel('2.4'), '2.4ghz', 'network labels the 2.4GHz band')
assertEqual(network.bandLabel('6'), '6ghz', 'network labels the 6GHz band')
assertEqual(network.bandLabel('auto'), 'Auto', 'network labels the automatic band choice')

assertEqual(network.bandSectionTitle('auto', '2.4'), 'WI-FI BAND: 2.4GHZ', 'network names the live band in the header under automatic')
assertEqual(network.bandSectionTitle('auto', ''), 'WI-FI BAND', 'network omits an unknown band from the header')
assertEqual(network.bandSectionTitle('5', '5'), 'WI-FI BAND', 'network drops the header band once the pills are showing')
assertEqual(network.bandSectionTitle('5', '2.4'), 'WI-FI BAND', 'network keeps a plain header while a pin is settling')

assertDeepEqual(
  network.parseBandStatus('band\t5\navailable\t2.4 5 6\nselected\tauto\n'),
  { band: '5', selected: 'auto', available: ['2.4', '5', '6'] },
  'network parses band status'
)
assertDeepEqual(
  network.parseBandStatus(''),
  { band: '', selected: 'auto', available: [] },
  'network parses empty band status without a wifi connection'
)



assertEqual(network.headerDetail({ type: 'wifi', freq: '5745' }), '', 'network keeps wifi band state out of the hero')
assertEqual(network.headerDetail({ type: 'ethernet', speed: '100' }), '100mbit', 'network keeps ethernet speed in the hero')

assertDeepEqual(
  network.parseAutoConnectProfiles(
    'uuid-home:802-11-wireless:yes:100:no\n' +
    'uuid-backup:802-11-wireless:no:200:yes\n' +
    'uuid-wired:802-3-ethernet:yes:300:yes\n'
  ),
  {
    'uuid-home': { uuid: 'uuid-home', enabled: true, timestamp: 100, active: false },
    'uuid-backup': { uuid: 'uuid-backup', enabled: false, timestamp: 200, active: true }
  },
  'network parses one UUID-keyed map without transporting SSIDs'
)

const selectionProfiles = network.parseAutoConnectProfiles(
  'uuid-active:802-11-wireless:no:10:yes\n' +
  'uuid-newest:802-11-wireless:yes:30:no\n' +
  'uuid-old:802-11-wireless:yes:20:no\n'
)
assertEqual(
  network.selectAutoConnectProfile(['uuid-old', 'uuid-newest', 'uuid-active'], selectionProfiles).uuid,
  'uuid-active',
  'network selects the single active profile before a newer inactive profile'
)
const multipleActiveProfiles = network.parseAutoConnectProfiles(
  'uuid-active-a:802-11-wireless:yes:10:yes\n' +
  'uuid-active-b:802-11-wireless:no:20:yes\n' +
  'uuid-inactive:802-11-wireless:yes:99:no\n'
)
assertEqual(
  network.selectAutoConnectProfile(['uuid-active-a', 'uuid-active-b', 'uuid-inactive'], multipleActiveProfiles),
  undefined,
  'network leaves multiple matching active profiles unresolved instead of falling through to an inactive profile'
)
assertEqual(
  network.selectAutoConnectProfile(['uuid-old', 'uuid-newest'], selectionProfiles).uuid,
  'uuid-newest',
  'network selects the newest profile when none is active'
)
const tiedProfiles = network.parseAutoConnectProfiles(
  'uuid-a:802-11-wireless:yes:50:no\n' +
  'uuid-b:802-11-wireless:no:50:no\n'
)
assertEqual(
  network.selectAutoConnectProfile(['uuid-a', 'uuid-b'], tiedProfiles),
  undefined,
  'network leaves an equal-timestamp profile tie unresolved'
)
assertEqual(
  network.selectAutoConnectProfile(['missing'], selectionProfiles),
  undefined,
  'network leaves a row unresolved when none of its snapshotted UUIDs exist'
)
assertEqual(
  network.selectAutoConnectProfile({ 0: 'uuid-old', 1: 'uuid-newest', 2: 'uuid-active', length: 3 }, selectionProfiles)?.uuid,
  'uuid-active',
  'network accepts indexed UUID sequences returned by QML list delegates'
)
for (const value of [null, undefined, 'uuid-active', 3, {}, { length: '1' }, { length: -1 }, { length: 0.5 }, { length: Infinity }, { length: NaN }]) {
  assertEqual(
    network.selectAutoConnectProfile(value, selectionProfiles),
    undefined,
    'network rejects an invalid UUID collection: ' + String(value)
  )
}
let coercedUuid = false
const nonPrimitiveUuid = { toString() { coercedUuid = true; return 'uuid-active' } }
assertEqual(
  network.selectAutoConnectProfile([nonPrimitiveUuid, null, undefined, 42, 'uuid-newest', 'uuid-newest'], selectionProfiles)?.uuid,
  'uuid-newest',
  'network ignores non-string UUID entries and duplicate profile references'
)
assertEqual(coercedUuid, false, 'network never coerces an object into a profile UUID')

const autoConnectSwitchSource = panelSource.match(/ToggleSwitch \{[\s\S]*?visible: row\.isKnown && row\.autoConnectProfile !== undefined[\s\S]*?PanelToolTip \{\s*visible: ([^\n]+)/)
assert(autoConnectSwitchSource, 'network has the auto-connect switch tooltip')
assert(/id: autoConnectSwitch/.test(autoConnectSwitchSource[0]), 'network names the auto-connect switch as the stable tooltip hover owner')
const tooltipVisible = new Function('parent', 'autoConnectSwitch', 'row', 'return ' + autoConnectSwitchSource[1])
assertEqual(tooltipVisible(null, { containsMouse: true }, { autoConnectFocused: false }), true, 'network auto-connect tooltip reads hover without a Popup parent')
assertEqual(tooltipVisible(null, { containsMouse: false }, { autoConnectFocused: true }), true, 'network auto-connect tooltip remains visible for keyboard focus')
assertEqual(tooltipVisible(null, { containsMouse: false }, { autoConnectFocused: false }), false, 'network auto-connect tooltip hides without hover or keyboard focus')

assertDeepEqual(
  network.autoConnectProfilesCommand,
  ['nmcli', '-t', '--escape', 'no', '-f', 'UUID,TYPE,AUTOCONNECT,TIMESTAMP,ACTIVE', 'connection', 'show'],
  'network reads all auto-connect state with one direct nmcli command'
)
assert(
  !/SSID|802-11-wireless\.ssid/.test(network.autoConnectProfilesCommand.join(' ')),
  'network auto-connect refresh does not transport SSIDs or secrets'
)
assert(
  /Model\.selectAutoConnectProfile\(net\.profileUuids, autoConnectProfiles\)/.test(panelSource),
  'network rows resolve auto-connect profiles from their snapshotted UUIDs'
)
assert(/ToggleSwitch[\s\S]*?visible: row\.isKnown && row\.autoConnectProfile !== undefined/.test(panelSource), 'known visible networks show an auto-connect switch when a profile exists')
assert(/id: autoConnectProfilesProc[\s\S]*?command: Model\.autoConnectProfilesCommand/.test(panelSource), 'network loads auto-connect profiles with one panel-level command')
const setAutoConnectFn = panelSource.match(/function setAutoConnect\(uuid, enabled\)[\s\S]*?\n {2}\}/)
assert(setAutoConnectFn, 'network has an auto-connect write helper')
assert(/"uuid", uuid, "connection\.autoconnect"/.test(setAutoConnectFn[0]), 'network writes auto-connect by stable NetworkManager UUID')
assert(!/disconnect|connection["', ]+down/.test(setAutoConnectFn[0]), 'network auto-connect writes never disconnect an active network')

const refreshAutoConnectFn = panelSource.match(/function refreshAutoConnectProfiles\(\)[\s\S]*?\n {2}\}/)
assert(refreshAutoConnectFn, 'network has an auto-connect refresh helper')
var autoConnectProfilesProc = { running: true }
var autoConnectRefreshPending = false
eval(refreshAutoConnectFn[0])
refreshAutoConnectProfiles()
assert(
  autoConnectProfilesProc.running && autoConnectRefreshPending,
  'network records one pending refresh instead of starting a second concurrent query'
)
autoConnectProfilesProc.running = false
refreshAutoConnectProfiles()
assert(
  autoConnectProfilesProc.running && !autoConnectRefreshPending,
  'network consumes the pending refresh when it starts the next query'
)
assert(
  /property bool autoConnectRefreshPending: false/.test(panelSource) &&
    /function refreshAutoConnectProfiles\(\)[\s\S]*?autoConnectProfilesProc\.running[\s\S]*?autoConnectRefreshPending = true/.test(panelSource) &&
    /id: autoConnectProfilesProc[\s\S]*?onExited:[\s\S]*?autoConnectRefreshPending[\s\S]*?refreshAutoConnectProfiles/.test(panelSource),
  'network queues one follow-up profile refresh while the panel query is running'
)
assert(
  /id: autoConnectChangeProc[\s\S]*?onExited:[\s\S]*?refreshAutoConnectProfiles\(\)/.test(panelSource),
  'network refreshes profile state after successful and failed writes'
)

assert(/property int wifiActionIndex: 0/.test(panelSource), 'network tracks row, auto-connect, and Forget as keyboard actions')
assert(
  /onAutoConnectProfilesChanged:\s*wifiActionIndex = 0/.test(panelSource),
  'network resets to the row action when profile topology changes so Enter cannot reinterpret auto-connect as Forget or vice versa'
)
assert(
  /function selectWifiActionByDelta\(delta\)[\s\S]*?wifiActionIndex/.test(panelSource),
  'network h/l navigation can move between wifi row actions'
)
assert(
  /function activateSelected\(\)[\s\S]*?setAutoConnect\(autoConnectProfile\.uuid[\s\S]*?forget\(net\)/.test(panelSource),
  'network Enter and Space activate auto-connect or Forget without replacing the row action'
)
assert(
  /readonly property bool autoConnectFocused:[^\n]*wifiActionIndex/.test(panelSource) &&
    /ToggleSwitch[\s\S]*?hasCursor: root\.cursorActive && row\.autoConnectFocused/.test(panelSource),
  'network gives the keyboard-focused auto-connect switch a visible cursor'
)
assert(
  /onHovered:[\s\S]{0,160}setWifiActionCursor/.test(panelSource) &&
    /id: rightMouse[\s\S]*?onContainsMouseChanged:[^\n]*wifiForgetActionIndex/.test(panelSource),
  'network mouse hover synchronizes the same auto-connect and Forget cursor model'
)
JS
