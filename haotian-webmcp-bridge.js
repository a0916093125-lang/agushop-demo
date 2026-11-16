/*!
 * HaoTian WebMCP & UCP v1.1 Agentic Commerce Bridge for 阿姑的店 AGU SHOP
 * Version: 3.0.0 | Guided Model Configurator + Power Ecosystem Ready
 */
(function () {
  'use strict';

  var BRIDGE_VERSION = '3.0.0';

  function registerModelContextTools(api) {
    try {
      if (typeof navigator !== 'undefined' && navigator.modelContext && typeof navigator.modelContext.registerTool === 'function') {
        navigator.modelContext.registerTool({
          name: 'agu_list_catalog',
          description: '查詢阿姑的店支援手機／筆電型號清單（含 iPhone 17 Pro Max 等）與全部 18 款三件套防護方案、快充線、氮化鎵充電頭、行動電源價格規格',
          inputSchema: {
            type: 'object',
            properties: {
              deviceModelId: { type: 'string', description: '機型代碼（如 ip17pm, ip14_13, s26u, mba15, mbp14）' },
              category: { type: 'string', description: 'all | phone_bundle | laptop_bundle | single_optical | power_addon' },
              query: { type: 'string', description: '搜尋關鍵字（如 iPhone 17 Pro Max、藍寶石、充電頭、行動電源）' }
            }
          },
          execute: function (args) { return Promise.resolve(api.listCatalog(args || {})); }
        });
        navigator.modelContext.registerTool({
          name: 'agu_manage_cart',
          description: '指定手機或筆電具體型號（如 iPhone 17 Pro Max），將三件套或充電線／充電頭／行動電源加入購物車，並取得含運總價與防偽檢核碼',
          inputSchema: {
            type: 'object',
            properties: {
              sku: { type: 'string', description: '商品編號 AGU-01 至 AGU-19' },
              deviceModel: { type: 'string', description: '機型名稱或代碼（如 iPhone 17 Pro Max 或 ip17pm）' },
              qty: { type: 'integer', description: '數量 (1-99)' },
              shippingMode: { type: 'string', enum: ['cvs', 'tw_home', 'bade_pickup', 'corp_batch'] },
              replaceCart: { type: 'boolean', description: '是否先清空既有購物車' }
            }
          },
          execute: function (args) { return Promise.resolve(api.applyAgentOrder(args || {})); }
        });
      }
    } catch (e) {}
  }

  window.initAguWebMCP = function (hooks) {
    if (!hooks) return null;
    var baseUrl = (hooks.getBaseUrl && hooks.getBaseUrl()) || 'https://a0916093125-lang.github.io/agushop-demo/';
    var api = {
      version: BRIDGE_VERSION,
      merchantId: 'tw-bade82-agushop',
      ucpEndpoint: baseUrl + '.well-known/ucp',
      llmsEndpoint: baseUrl + 'llms.txt',
      listDevices: function (query) {
        var q = String(query || '').trim().toLowerCase();
        return hooks.getDevices().filter(function (d) {
          if (!q) return true;
          return (d.id + ' ' + d.brand + ' ' + d.name + ' ' + d.note).toLowerCase().indexOf(q) !== -1;
        });
      },
      listCatalog: function (filter) {
        var opts = filter || {};
        if (opts.deviceModelId && hooks.selectDevice) {
          hooks.selectDevice(opts.deviceModelId);
        }
        var cat = opts.category || 'all';
        var q = String(opts.query || '').trim().toLowerCase();
        return hooks.getCatalog().filter(function (it) {
          if (cat !== 'all' && it.category !== cat) return false;
          if (!q) return true;
          var hay = (it.id + ' ' + it.name + ' ' + it.material + ' ' + it.spec + ' ' + (it.keywords || '')).toLowerCase();
          return hay.indexOf(q) !== -1;
        });
      },
      getCartSummary: function () { return hooks.getSummary(); },
      selectDevice: function (modelIdOrName) { return hooks.selectDevice(modelIdOrName); },
      addToCart: function (sku, qty, modelName) { return hooks.addItem(sku, qty || 1, modelName); },
      clearCart: function () { return hooks.clearCart(); },
      applyAgentOrder: function (payload) { return hooks.applyExternalOrder(payload || {}); }
    };
    window.HaotianWebMCP = api;
    registerModelContextTools(api);
    return api;
  };
})();
