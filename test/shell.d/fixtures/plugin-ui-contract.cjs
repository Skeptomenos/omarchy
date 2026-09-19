// Run real QML JavaScript bodies with synthetic configuration and window geometry.
// This covers dispatch and settings behavior without starting the desktop shell.
const assert = require('node:assert/strict')
const fs = require('node:fs')
const path = require('node:path')
const vm = require('node:vm')

function functionSource(text, name, indent = 2) {
  const pad = ' '.repeat(indent)
  const match = text.match(new RegExp(`^${pad}function ${name}\\([^]*?^${pad}\\}`, 'm'))
  assert(match, `missing QML function ${name}`)
  return match[0]
}

function install(text, names, context, receiver, indent = 2) {
  for (const name of names) {
    vm.runInContext(functionSource(text, name, indent), context)
    receiver[name] = context[name]
  }
}

function createHost(root, config, manifests) {
  const read = name => fs.readFileSync(path.join(root, name), 'utf8')
  const Util = {
    isPlainObject: value => !!value && typeof value === 'object' && !Array.isArray(value),
    canonicalWidgetId: value => value
  }
  const registry = {
    installedPlugins: manifests, resolveEnabledId: id => id,
    isEnabled: id => !!manifests[id], barEntryId: entry => entry.id
  }
  const rc = vm.createContext({ Util, ...registry })
  install(read('shell/services/PluginRegistry.qml'), ['findBarLocation', 'findEntryLocation'], rc, registry)
  const writes = [], actions = []
  const ownService = { marker: 'own' }
  const host = {
    shellConfig: config, pluginRegistry: registry,
    publicBarConfig: () => JSON.parse(JSON.stringify(host.shellConfig.bar)),
    pluginBarStateFor: () => ({}), publicPluginManifest: m => m,
    prunePluginApis() {}, serviceFor: () => ownService,
    summon: id => (actions.push(['summon', id]), true),
    hide: id => (actions.push(['hide', id]), true),
    toggle: id => (actions.push(['toggle', id]), true), isPluginOpen: () => true
  }
  const hc = vm.createContext({
    shell: host, Util, shellConfig: config,
    _pluginShellApis: {}, _pluginShellApiDescriptors: {}, _pluginRegistryApis: {},
    _pluginBarWidgetRegistryApis: {}, _pluginBarEntryShellApis: {},
    pluginShellApiComponent: { createObject: (_, props) => props },
    persistShellConfig: next => {
      writes.push(next)
      host.shellConfig = hc.shellConfig = next
      host.syncPluginApis()
    }
  })
  install(read('shell/shell.qml'), [
    'pluginSettingsFor', 'manifestHasKind', 'pluginHasBarCapabilities', 'publicIdleConfigFor',
    'pluginCloneMaySummon', 'pluginOwnsTarget', 'pluginServiceFor', 'barPluginMayControl',
    'pluginShellCapabilityProfile', 'createScopedPluginShell', 'syncPluginApis', 'updateEntryInline'
  ], hc, host)
  function facade(id) {
    const api = host.createScopedPluginShell(manifests[id], id, true, false)
    const ac = vm.createContext({ ...api })
    install(read('shell/services/PluginShellApi.qml'), [
      'serviceFor', 'summon', 'hide', 'toggle', 'isPluginOpen', 'updateEntryInline'
    ], ac, api)
    return api
  }
  return { host, context: hc, facade, writes, actions, ownService }
}

function testSettings(root) {
  const config = {
    bar: { layout: { left: [], center: [], right: [{ id: 'fixture.widget', size: 42 }] } },
    plugins: [
      { id: 'fixture.panel', iconSize: 64, pinned: ['fixture-app'] },
      { id: 'fixture.peer', privateMarker: 'peer-only' }
    ]
  }
  const manifests = Object.fromEntries(['fixture.panel', 'fixture.peer'].map(id => [id, { id, kinds: ['panel'] }]))
  const { host, facade, writes } = createHost(root, config, manifests)
  const api = facade('fixture.panel')
  assert.equal(JSON.stringify(api.settings), JSON.stringify({ iconSize: 64, pinned: ['fixture-app'] }))
  api.settings.pinned.push('local-only')
  assert.deepEqual(config.plugins[0].pinned, ['fixture-app'])
  api.pluginId = 'fixture.peer'
  host.syncPluginApis()
  assert.equal(api.settings.privateMarker, undefined)
  assert.equal(JSON.stringify(api.settings.pinned), '["fixture-app"]')
  const settings = JSON.parse(JSON.stringify(api.settings))
  settings.monochrome = false
  assert.equal(api.updateEntryInline('fixture.panel', settings), true)
  assert.equal(JSON.stringify(writes[0].plugins), JSON.stringify([
    { id: 'fixture.panel', iconSize: 64, pinned: ['fixture-app'], monochrome: false },
    { id: 'fixture.peer', privateMarker: 'peer-only' }
  ]))
  assert.equal(api.settings.monochrome, false)
  host.shellConfig.plugins[0].iconSize = 48
  host.syncPluginApis()
  assert.equal(api.settings.iconSize, 48)
  assert.equal(api.updateEntryInline('fixture.peer', {}), false)
  assert.equal(api.serviceFor('omarchy.lock'), null)
  assert.equal(host.pluginSettingsFor('fixture.widget').size, 42)
  assert.equal(Object.keys(host.pluginSettingsFor('missing')).length, 0)
  console.log('ok - own settings detach nested data, refresh by trusted identity, and preserve saved fields')
}

function testClicks(root) {
  const read = name => fs.readFileSync(path.join(root, name), 'utf8')
  const barText = read('shell/plugins/bar/Bar.qml')
  const panelText = read('shell/Ui/KeyboardPanel.qml')
  const Qt = { LeftButton: 1, RightButton: 2, MiddleButton: 4, point: (x, y) => ({ x, y }) }
  const window = { width: 100, height: 30, contentItem: {}, itemPosition: item => item }
  const otherWindow = { ...window, contentItem: {} }
  const clicked = []
  function button(id, x, ownerWindow = window) {
    return { id, x, y: 0, width: 20, height: 20, window: ownerWindow, parent: null,
      visible: true, opacity: 1, triggerPress: code => clicked.push([id, code]) }
  }
  const own = button('fixture.own', 0), peer = button('fixture.peer', 30)
  const auth = button('omarchy.lock', 60), remote = button('fixture.remote', 80, otherWindow)
  const orphan = button('fixture.unmounted', 80)
  const peerWidget = { parent: null }
  peer.parent = peerWidget
  const popout = { window }
  const manifests = Object.fromEntries([own, peer, auth, remote].map(item => [item.id, { id: item.id }]))
  const host = {
    pluginRegistry: { installedPlugins: manifests, isEnabled: id => !!manifests[id] },
    isAuthenticationService: (_, id) => id === 'omarchy.lock',
    pluginShellForId: () => ({})
  }
  const bar = {
    shell: host, pluginBarApis: {}, clickTargets: [own, peer, auth, remote, orphan], activePopout: popout,
    moduleSlots: [own, peer, auth, remote].map(item => ({ activeItem: item === peer ? peerWidget : item, moduleName: item.id,
      visible: true, width: 20, height: 20, registered: true })),
    pluginObjectRecord: item => item === own ? { pluginId: 'fixture.own', clickTarget: true }
      : item === popout ? { pluginId: 'fixture.own', popout: true } : null,
    targetWindow: item => item && item.window,
    targetBelongsToWindow: (item, candidate) => item.window === candidate,
    sameWindow: (a, b) => !!a && a === b,
    canonicalWidgetId: id => id,
    bindPluginBarApi(api) { api.clickTargets = bar.pluginClickTargets('fixture.own') }
  }
  const bc = vm.createContext({
    root: bar, Qt, moduleSlots: bar.moduleSlots, pluginBarApis: bar.pluginBarApis,
    pluginBarApiComponent: { createObject: (_, props) => props }
  })
  install(barText, ['pluginOwnsBarObject', 'pluginClickTargets', 'pluginBarApiFor',
    'moduleTargetClickable', 'barClickTargetAllowed', 'forwardBarClick'], bc, bar)
  const api = bar.pluginBarApiFor('fixture.own', 'fixture.own', true)
  const ac = vm.createContext({ ...api })
  install(read('shell/Ui/PluginBarApi.qml'), ['forwardBarClick'], ac, api)
  api.pluginId = 'fixture.peer'
  let closes = 0
  const panel = { bar: api, anchorItem: own, anchorWindow: window,
    barPos: 'top', _barStripSize: 30, barH: 30, barW: 100,
    screenW: 100, screenH: 200, focusPrimed: true, close: () => closes++ }
  const pc = vm.createContext({ root: panel, Qt })
  install(panelText, ['barPoint', 'inBarRegion', 'pressTargetAt', 'forwardBarClick'], pc, pc, 4)
  const handler = panelText.match(/^    onClicked: function\(mouse\) \{([^]*?)^    \}/m)
  assert(handler, 'actual KeyboardPanel click handler')
  vm.runInContext(`function clicked(mouse) {${handler[1]}}`, pc)
  pc.clicked({ x: 35, y: 5, button: Qt.LeftButton })
  assert.deepEqual(clicked, [['fixture.peer', Qt.LeftButton]])
  assert.equal(closes, 0)
  assert.equal(api.clickTargets.length, 1)
  assert.equal(api.clickTargets[0], own)
  panel.barPos = 'bottom'
  pc.clicked({ x: 35, y: 175, button: Qt.RightButton })
  assert.deepEqual(clicked[1], ['fixture.peer', Qt.RightButton])
  panel.barPos = 'top'
  pc.clicked({ x: 65, y: 5, button: Qt.LeftButton })
  assert.equal(closes, 1)
  assert.equal(clicked.length, 2)
  for (const args of [[peer, 35, 5, 1], [own, 85, 5, 1], [own, -1, 5, 1],
    [own, NaN, 5, 1], [own, '35', 5, 1], [own, 35, 5, 99]]) {
    assert.equal(api._forwardBarClick(...args), false)
  }
  peer.concealed = true
  assert.equal(api.forwardBarClick(own, 35, 5, 1), false)
  peer.concealed = false
  delete manifests[peer.id]
  assert.equal(api.forwardBarClick(own, 35, 5, 1), false)
  bar.activePopout = null
  assert.equal(api.forwardBarClick(own, 35, 5, 1), false)
  assert.equal(clicked.length, 2)
  console.log('ok - actual KeyboardPanel handler forwards through the scoped callback without exposing targets')
  console.log('ok - forwarding rejects foreign anchors, authentication UI, other windows, invalid input, hidden UI, and inactive owners')
}

module.exports = { createHost, functionSource, install }
if (require.main === module) {
  const root = process.argv[2]
  testSettings(root)
  testClicks(root)
}
