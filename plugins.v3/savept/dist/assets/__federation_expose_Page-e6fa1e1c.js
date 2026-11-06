import { importShared } from './__federation_fn_import-054b33c3.js';
import { _ as _export_sfc, b as buildNoticeSections, t as tokenizeNoticeText, p as pluginRequest } from './_plugin-vue_export-helper-d1e0ed3a.js';

const Page_vue_vue_type_style_index_0_scoped_452c5ee8_lang = '';

const {resolveComponent:_resolveComponent,createVNode:_createVNode,createElementVNode:_createElementVNode,withCtx:_withCtx,toDisplayString:_toDisplayString,normalizeClass:_normalizeClass,openBlock:_openBlock,createElementBlock:_createElementBlock,createCommentVNode:_createCommentVNode,Transition:_Transition,createTextVNode:_createTextVNode,renderList:_renderList,Fragment:_Fragment,unref:_unref} = await importShared('vue');


const _hoisted_1 = { class: "spg-page" };
const _hoisted_2 = { class: "spg-topbar" };
const _hoisted_3 = { class: "spg-topbar__left" };
const _hoisted_4 = { class: "spg-topbar__icon" };
const _hoisted_5 = { class: "spg-topbar__right" };
const _hoisted_6 = { class: "spg-summary" };
const _hoisted_7 = { class: "spg-vitals" };
const _hoisted_8 = { class: "spg-vital spg-vital--total" };
const _hoisted_9 = { class: "spg-vital__head" };
const _hoisted_10 = { class: "spg-vital__icon" };
const _hoisted_11 = { class: "spg-vital__value" };
const _hoisted_12 = { class: "spg-vital spg-vital--healthy" };
const _hoisted_13 = { class: "spg-vital__head" };
const _hoisted_14 = { class: "spg-vital__icon" };
const _hoisted_15 = { class: "spg-vital__value" };
const _hoisted_16 = { class: "spg-vital spg-vital--critical" };
const _hoisted_17 = { class: "spg-vital__head" };
const _hoisted_18 = { class: "spg-vital__icon" };
const _hoisted_19 = { class: "spg-vital__value" };
const _hoisted_20 = { class: "spg-vital spg-vital--closed" };
const _hoisted_21 = { class: "spg-vital__head" };
const _hoisted_22 = { class: "spg-vital__icon" };
const _hoisted_23 = { class: "spg-vital__value" };
const _hoisted_24 = { class: "spg-summary-pills" };
const _hoisted_25 = { class: "spg-summary-pill spg-summary-pill--anniv" };
const _hoisted_26 = { class: "spg-summary-pill__value" };
const _hoisted_27 = { class: "spg-summary-pill spg-summary-pill--internal" };
const _hoisted_28 = { class: "spg-summary-pill__value" };
const _hoisted_29 = { class: "spg-summary-pill spg-summary-pill--external" };
const _hoisted_30 = { class: "spg-summary-pill__value" };
const _hoisted_31 = { class: "spg-summary-pill spg-summary-pill--years" };
const _hoisted_32 = { class: "spg-summary-pill__value" };
const _hoisted_33 = {
  key: 0,
  class: "spg-warning"
};
const _hoisted_34 = { class: "spg-card spg-card--panel" };
const _hoisted_35 = { class: "spg-card__header" };
const _hoisted_36 = { class: "spg-card__title d-flex align-center" };
const _hoisted_37 = {
  key: 0,
  class: "spg-card__badge d-flex align-center"
};
const _hoisted_38 = { class: "spg-notices" };
const _hoisted_39 = { class: "spg-notice-card__title" };
const _hoisted_40 = {
  key: 0,
  class: "spg-notice-card__content"
};
const _hoisted_41 = { key: 1 };
const _hoisted_42 = {
  key: 1,
  class: "spg-notice-card__empty"
};

const {computed,onBeforeUnmount,onMounted,reactive,ref} = await importShared('vue');


const _sfc_main = {
  __name: 'Page',
  props: {
  api: { type: Object, default: () => ({}) },
  initialConfig: { type: Object, default: () => ({}) },
},
  emits: ['switch', 'close'],
  setup(__props, { emit: __emit }) {

const props = __props;
const emit = __emit;

const loading = reactive({ overview: false });
const message = reactive({ show: false, type: 'info', text: '' });
const summary = reactive({ total: 0, healthy: 0, critical: 0, closed: 0, internal: 0, external: 0, today_anniv: 0, years: 0, mp_owned: 0 });
const alerts = ref([]);
const sites = ref([]);
const fetchedAt = ref('');
const warning = ref('');

const noticeSections = computed(() => buildNoticeSections(alerts.value));
let messageTimer = null;

function clearMessageTimer() {
  if (messageTimer) {
    clearTimeout(messageTimer);
    messageTimer = null;
  }
}

function scheduleMessageClose(type = 'info') {
  clearMessageTimer();
  const timeout = type === 'error' ? 5000 : 3000;
  messageTimer = setTimeout(() => {
    message.show = false;
    messageTimer = null;
  }, timeout);
}

function pushMessage(text, type = 'info') {
  message.text = text;
  message.type = type;
  message.show = true;
  scheduleMessageClose(type);
}

async function fetchOverview(showSuccess = false) {
  loading.overview = true;
  try {
    const result = await pluginRequest(props.api, '/sites', { method: 'GET' });
    if (!result?.success) {
      throw new Error(result?.message || '加载页面数据失败')
    }

    const data = result.data || {};
    Object.assign(summary, data.summary || {});
    alerts.value = data.alerts || [];
    sites.value = data.sites || [];
    fetchedAt.value = data.fetched_at || '';
    warning.value = data.warning || '';

    if (showSuccess) {
      pushMessage('页面数据已刷新', 'success');
    }
  } catch (error) {
    pushMessage(error.message || '加载页面数据失败', 'error');
  } finally {
    loading.overview = false;
  }
}

onMounted(() => {
  fetchOverview();
});

onBeforeUnmount(() => {
  clearMessageTimer();
});

return (_ctx, _cache) => {
  const _component_v_icon = _resolveComponent("v-icon");
  const _component_v_btn = _resolveComponent("v-btn");
  const _component_v_btn_group = _resolveComponent("v-btn-group");

  return (_openBlock(), _createElementBlock("div", _hoisted_1, [
    _createElementVNode("div", _hoisted_2, [
      _createElementVNode("div", _hoisted_3, [
        _createElementVNode("div", _hoisted_4, [
          _createVNode(_component_v_icon, {
            icon: "mdi-heart-pulse",
            size: "24"
          })
        ]),
        _cache[4] || (_cache[4] = _createElementVNode("div", { class: "spg-topbar__meta" }, [
          _createElementVNode("div", { class: "spg-topbar__title" }, "PT 监护室"),
          _createElementVNode("div", { class: "spg-topbar__sub" }, "实时统计、关键公告与站点运行概览")
        ], -1))
      ]),
      _createElementVNode("div", _hoisted_5, [
        _createVNode(_component_v_btn_group, {
          variant: "tonal",
          density: "compact",
          class: "spg-btn-group elevation-0"
        }, {
          default: _withCtx(() => [
            _createVNode(_component_v_btn, {
              color: "primary",
              onClick: _cache[0] || (_cache[0] = $event => (fetchOverview(true))),
              loading: loading.overview,
              size: "small",
              "min-width": "40",
              class: "px-0 px-sm-3"
            }, {
              default: _withCtx(() => [
                _createVNode(_component_v_icon, {
                  icon: "mdi-refresh",
                  size: "18",
                  class: "mr-sm-1"
                }),
                _cache[5] || (_cache[5] = _createElementVNode("span", { class: "btn-text d-none d-sm-inline" }, "刷新", -1))
              ]),
              _: 1
            }, 8, ["loading"]),
            _createVNode(_component_v_btn, {
              color: "primary",
              onClick: _cache[1] || (_cache[1] = $event => (emit('switch'))),
              size: "small",
              "min-width": "40",
              class: "px-0 px-sm-3"
            }, {
              default: _withCtx(() => [
                _createVNode(_component_v_icon, {
                  icon: "mdi-cog",
                  size: "18",
                  class: "mr-sm-1"
                }),
                _cache[6] || (_cache[6] = _createElementVNode("span", { class: "btn-text d-none d-sm-inline" }, "设置", -1))
              ]),
              _: 1
            }),
            _createVNode(_component_v_btn, {
              color: "primary",
              onClick: _cache[2] || (_cache[2] = $event => (emit('close'))),
              size: "small",
              "min-width": "40",
              class: "px-0 px-sm-3"
            }, {
              default: _withCtx(() => [
                _createVNode(_component_v_icon, {
                  icon: "mdi-close",
                  size: "18"
                }),
                _cache[7] || (_cache[7] = _createElementVNode("span", { class: "btn-text d-none d-sm-inline" }, "关闭", -1))
              ]),
              _: 1
            })
          ]),
          _: 1
        })
      ])
    ]),
    _createVNode(_Transition, { name: "spg-slide" }, {
      default: _withCtx(() => [
        (message.show)
          ? (_openBlock(), _createElementBlock("div", {
              key: 0,
              class: _normalizeClass(["spg-toast", `spg-toast--${message.type}`])
            }, [
              _createVNode(_component_v_icon, {
                icon: message.type === 'success' ? 'mdi-check-circle' : message.type === 'error' ? 'mdi-alert-circle' : 'mdi-information',
                size: "18"
              }, null, 8, ["icon"]),
              _createElementVNode("span", null, _toDisplayString(message.text), 1),
              _createElementVNode("button", {
                class: "spg-toast__close",
                onClick: _cache[3] || (_cache[3] = $event => (message.show = false))
              }, [
                _createVNode(_component_v_icon, {
                  icon: "mdi-close",
                  size: "16"
                })
              ])
            ], 2))
          : _createCommentVNode("", true)
      ]),
      _: 1
    }),
    _createElementVNode("div", _hoisted_6, [
      _createElementVNode("div", _hoisted_7, [
        _createElementVNode("div", _hoisted_8, [
          _createElementVNode("div", _hoisted_9, [
            _createElementVNode("span", _hoisted_10, [
              _createVNode(_component_v_icon, {
                icon: "mdi-monitor-dashboard",
                size: "16"
              })
            ]),
            _cache[8] || (_cache[8] = _createElementVNode("span", { class: "spg-vital__label" }, "监护中", -1))
          ]),
          _createElementVNode("div", _hoisted_11, _toDisplayString(summary.total), 1)
        ]),
        _createElementVNode("div", _hoisted_12, [
          _createElementVNode("div", _hoisted_13, [
            _createElementVNode("span", _hoisted_14, [
              _createVNode(_component_v_icon, {
                icon: "mdi-heart-pulse",
                size: "16"
              })
            ]),
            _cache[9] || (_cache[9] = _createElementVNode("span", { class: "spg-vital__label" }, "健康站点", -1))
          ]),
          _createElementVNode("div", _hoisted_15, _toDisplayString(summary.healthy), 1)
        ]),
        _createElementVNode("div", _hoisted_16, [
          _createElementVNode("div", _hoisted_17, [
            _createElementVNode("span", _hoisted_18, [
              _createVNode(_component_v_icon, {
                icon: "mdi-alert-circle",
                size: "16"
              })
            ]),
            _cache[10] || (_cache[10] = _createElementVNode("span", { class: "spg-vital__label" }, "病危站点", -1))
          ]),
          _createElementVNode("div", _hoisted_19, _toDisplayString(summary.critical), 1)
        ]),
        _createElementVNode("div", _hoisted_20, [
          _createElementVNode("div", _hoisted_21, [
            _createElementVNode("span", _hoisted_22, [
              _createVNode(_component_v_icon, {
                icon: "mdi-skull-outline",
                size: "16"
              })
            ]),
            _cache[11] || (_cache[11] = _createElementVNode("span", { class: "spg-vital__label" }, "已关站", -1))
          ]),
          _createElementVNode("div", _hoisted_23, _toDisplayString(summary.closed), 1)
        ])
      ]),
      _createElementVNode("div", _hoisted_24, [
        _createElementVNode("div", _hoisted_25, [
          _createVNode(_component_v_icon, {
            icon: "mdi-party-popper",
            size: "15"
          }),
          _cache[12] || (_cache[12] = _createElementVNode("span", { class: "spg-summary-pill__text" }, "今日站庆", -1)),
          _createElementVNode("span", _hoisted_26, _toDisplayString(summary.today_anniv), 1)
        ]),
        _createElementVNode("div", _hoisted_27, [
          _createVNode(_component_v_icon, {
            icon: "mdi-home-city-outline",
            size: "15"
          }),
          _cache[13] || (_cache[13] = _createElementVNode("span", { class: "spg-summary-pill__text" }, "内站", -1)),
          _createElementVNode("span", _hoisted_28, _toDisplayString(summary.internal), 1)
        ]),
        _createElementVNode("div", _hoisted_29, [
          _createVNode(_component_v_icon, {
            icon: "mdi-earth",
            size: "15"
          }),
          _cache[14] || (_cache[14] = _createElementVNode("span", { class: "spg-summary-pill__text" }, "外站", -1)),
          _createElementVNode("span", _hoisted_30, _toDisplayString(summary.external), 1)
        ]),
        _createElementVNode("div", _hoisted_31, [
          _createVNode(_component_v_icon, {
            icon: "mdi-check-decagram",
            size: "15"
          }),
          _cache[15] || (_cache[15] = _createElementVNode("span", { class: "spg-summary-pill__text" }, "已拥有站点", -1)),
          _createElementVNode("span", _hoisted_32, _toDisplayString(summary.mp_owned), 1)
        ])
      ])
    ]),
    (warning.value)
      ? (_openBlock(), _createElementBlock("div", _hoisted_33, [
          _createVNode(_component_v_icon, {
            icon: "mdi-alert-outline",
            size: "18"
          }),
          _createElementVNode("span", null, _toDisplayString(warning.value), 1)
        ]))
      : _createCommentVNode("", true),
    _createElementVNode("div", _hoisted_34, [
      _createElementVNode("div", _hoisted_35, [
        _createElementVNode("span", _hoisted_36, [
          _createVNode(_component_v_icon, {
            icon: "mdi-bullhorn-outline",
            size: "18",
            color: "info",
            class: "mr-1"
          }),
          _cache[16] || (_cache[16] = _createTextVNode(" 站点公告 ", -1))
        ]),
        (fetchedAt.value)
          ? (_openBlock(), _createElementBlock("span", _hoisted_37, [
              _createVNode(_component_v_icon, {
                icon: "mdi-clock-outline",
                size: "14",
                class: "mr-1"
              }),
              _createTextVNode(" " + _toDisplayString(fetchedAt.value), 1)
            ]))
          : _createCommentVNode("", true)
      ]),
      _createElementVNode("div", _hoisted_38, [
        (_openBlock(true), _createElementBlock(_Fragment, null, _renderList(noticeSections.value, (section) => {
          return (_openBlock(), _createElementBlock("div", {
            key: section.key,
            class: _normalizeClass(["spg-notice-card", `spg-notice-card--${section.key}`])
          }, [
            _createElementVNode("div", _hoisted_39, _toDisplayString(section.title), 1),
            (section.items.length)
              ? (_openBlock(), _createElementBlock("div", _hoisted_40, [
                  (_openBlock(true), _createElementBlock(_Fragment, null, _renderList(section.items, (item, index) => {
                    return (_openBlock(), _createElementBlock("div", {
                      key: `${section.key}-${index}`,
                      class: "spg-notice-card__item"
                    }, [
                      (_openBlock(true), _createElementBlock(_Fragment, null, _renderList(_unref(tokenizeNoticeText)(item, sites.value), (token, tokenIndex) => {
                        return (_openBlock(), _createElementBlock(_Fragment, {
                          key: `${section.key}-${index}-${tokenIndex}`
                        }, [
                          (token.type === 'site')
                            ? (_openBlock(), _createElementBlock("span", {
                                key: 0,
                                class: _normalizeClass(["spg-notice-tag", `spg-notice-tag--${section.key}`])
                              }, _toDisplayString(token.text), 3))
                            : (_openBlock(), _createElementBlock("span", _hoisted_41, _toDisplayString(token.text), 1))
                        ], 64))
                      }), 128))
                    ]))
                  }), 128))
                ]))
              : (_openBlock(), _createElementBlock("div", _hoisted_42, "暂无公告"))
          ], 2))
        }), 128))
      ])
    ])
  ]))
}
}

};
const Page = /*#__PURE__*/_export_sfc(_sfc_main, [['__scopeId',"data-v-452c5ee8"]]);

export { Page as default };
