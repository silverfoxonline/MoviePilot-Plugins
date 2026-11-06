import { _ as __vitePreload } from './preload-helper-06b33f0f.js';
import { importShared } from './__federation_fn_import-054b33c3.js';
import { _ as _export_sfc, b as buildNoticeSections, a as buildSiteKeywords, g as getStatusMeta, t as tokenizeNoticeText, p as pluginRequest, c as getMpStatusMeta } from './_plugin-vue_export-helper-d1e0ed3a.js';

const AppPage_vue_vue_type_style_index_0_scoped_c7dff6f4_lang = '';

const AppPage_vue_vue_type_style_index_1_lang = '';

const {resolveComponent:_resolveComponent,createVNode:_createVNode,createElementVNode:_createElementVNode,toDisplayString:_toDisplayString,createTextVNode:_createTextVNode,openBlock:_openBlock,createBlock:_createBlock,createCommentVNode:_createCommentVNode,vModelText:_vModelText,withDirectives:_withDirectives,createElementBlock:_createElementBlock,normalizeClass:_normalizeClass,withModifiers:_withModifiers,renderList:_renderList,Fragment:_Fragment,unref:_unref,Transition:_Transition,withCtx:_withCtx,normalizeStyle:_normalizeStyle,vShow:_vShow,Teleport:_Teleport} = await importShared('vue');


const _hoisted_1 = { class: "spt-header" };
const _hoisted_2 = { class: "spt-header__top" };
const _hoisted_3 = { class: "spt-header__brand" };
const _hoisted_4 = { class: "spt-pulse-icon" };
const _hoisted_5 = { class: "spt-vitals" };
const _hoisted_6 = { class: "spt-vital spt-vital--total" };
const _hoisted_7 = { class: "spt-vital__value" };
const _hoisted_8 = { class: "spt-vital spt-vital--healthy" };
const _hoisted_9 = { class: "spt-vital__value" };
const _hoisted_10 = { class: "spt-vital spt-vital--owned" };
const _hoisted_11 = { class: "spt-vital__value" };
const _hoisted_12 = { class: "spt-vital spt-vital--critical" };
const _hoisted_13 = { class: "spt-vital__value" };
const _hoisted_14 = { class: "spt-vital spt-vital--closed" };
const _hoisted_15 = { class: "spt-vital__value" };
const _hoisted_16 = { class: "spt-vital spt-vital--anniv" };
const _hoisted_17 = { class: "spt-vital__value" };
const _hoisted_18 = { class: "spt-header__actions" };
const _hoisted_19 = { class: "spt-meta-pill" };
const _hoisted_20 = ["disabled"];
const _hoisted_21 = { class: "spt-header__filters" };
const _hoisted_22 = { class: "spt-filters__search" };
const _hoisted_23 = { class: "spt-filters__select-label" };
const _hoisted_24 = {
  key: 0,
  class: "spt-filters__dropdown"
};
const _hoisted_25 = ["onClick"];
const _hoisted_26 = { class: "spt-filters__select-label" };
const _hoisted_27 = {
  key: 0,
  class: "spt-filters__dropdown"
};
const _hoisted_28 = ["onClick"];
const _hoisted_29 = { class: "spt-filters__pills" };
const _hoisted_30 = ["onClick"];
const _hoisted_31 = { class: "spt-filters__pills" };
const _hoisted_32 = ["onClick"];
const _hoisted_33 = { class: "spt-filters__meta" };
const _hoisted_34 = {
  key: 0,
  class: "spt-filters__meta-time"
};
const _hoisted_35 = { class: "spt-filters__meta-count" };
const _hoisted_36 = { class: "spt-notices" };
const _hoisted_37 = { class: "spt-notice-card__title" };
const _hoisted_38 = {
  key: 0,
  class: "spt-notice-card__content"
};
const _hoisted_39 = { key: 1 };
const _hoisted_40 = {
  key: 1,
  class: "spt-notice-card__empty"
};
const _hoisted_41 = {
  key: 0,
  class: "spt-warning"
};
const _hoisted_42 = { class: "spt-year-group__header" };
const _hoisted_43 = ["onClick"];
const _hoisted_44 = { class: "spt-year-group__badge" };
const _hoisted_45 = { class: "spt-year-group__suffix" };
const _hoisted_46 = { class: "spt-year-group__count" };
const _hoisted_47 = ["onClick", "aria-label"];
const _hoisted_48 = { class: "spt-grid" };
const _hoisted_49 = ["href"];
const _hoisted_50 = {
  key: 0,
  class: "spt-card__celebration",
  "aria-hidden": "true"
};
const _hoisted_51 = { class: "spt-card__body" };
const _hoisted_52 = { class: "spt-card__badges" };
const _hoisted_53 = { class: "spt-card__badges-left" };
const _hoisted_54 = { class: "spt-tag spt-tag--type" };
const _hoisted_55 = {
  key: 0,
  class: "spt-tag spt-tag--duration"
};
const _hoisted_56 = { class: "spt-tag__text" };
const _hoisted_57 = { class: "spt-tag__text" };
const _hoisted_58 = { class: "spt-card__main" };
const _hoisted_59 = ["src", "alt"];
const _hoisted_60 = { class: "spt-card__info" };
const _hoisted_61 = { class: "spt-card__name-row" };
const _hoisted_62 = { class: "spt-card__name" };
const _hoisted_63 = { class: "spt-card__sub" };
const _hoisted_64 = {
  key: 0,
  class: "spt-card__sub spt-card__sub--mp"
};
const _hoisted_65 = {
  key: 0,
  class: "spt-card__mp-text"
};
const _hoisted_66 = {
  key: 1,
  class: "spt-empty"
};

const {computed,nextTick,onBeforeUnmount,onMounted,reactive,ref,watch} = await importShared('vue');


const _sfc_main = {
  __name: 'AppPage',
  props: {
  api: { type: Object, default: () => ({}) },
  navKey: { type: String, default: 'main' },
  pluginId: { type: String, default: '' },
},
  emits: [],
  setup(__props, { emit: __emit }) {

const props = __props;

const loading = ref(false);
const message = reactive({ show: false, type: 'info', text: '' });
const summary = reactive({ total: 0, healthy: 0, critical: 0, closed: 0, internal: 0, external: 0, today_anniv: 0, years: 0, mp_owned: 0, mp_available: 0, mp_unsupported: 0 });
const alerts = ref([]);
const sites = ref([]);
const yearGroups = ref([]);
const fetchedAt = ref('');
const warning = ref('');
const showBackToTop = ref(false);
const backTopStyle = ref({});
const prefersReducedMotion = ref(false);

const celebrationCanvasRefs = new Map();
const celebrationConfettiInstances = new Map();
const celebrationConfettiTimers = new Map();
let celebrationConfettiFactory = null;
let celebrationConfettiLoader = null;
let reducedMotionMediaQuery = null;

const statusOptions = [
  { label: '全部', value: '全部' },
  { label: '健康', value: '健康' },
  { label: '病危', value: '病危' },
  { label: '死亡', value: '死亡' },
];
const typeOptions = [
  { label: '全部', value: '全部' },
  { label: '内站', value: '内站' },
  { label: '外站', value: '外站' },
];
const mpFilterOptions = [
  { label: '全部', value: '全部' },
  { label: '已拥有', value: 'owned' },
  { label: '可添加', value: 'available' },
  { label: '未收录', value: 'unsupported' },
];

const filters = reactive({
  keyword: '',
  year: '全部',
  mpStatus: '全部',
  status: '全部',
  type: '全部',
  anniversaryOnly: false,
});

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

async function loadData(showSuccess = false) {
  loading.value = true;
  try {
    const result = await pluginRequest(props.api, '/sites', { method: 'GET' });
    if (!result?.success) {
      throw new Error(result?.message || '加载站点数据失败')
    }
    const data = result.data || {};
    Object.assign(summary, data.summary || {});
    alerts.value = data.alerts || [];
    sites.value = data.sites || [];
    yearGroups.value = data.year_groups || [];
    fetchedAt.value = data.fetched_at || '';
    warning.value = data.warning || '';
    if (data.default_internal_only) {
      filters.type = '内站';
    }
    if (showSuccess) {
      pushMessage('数据已刷新', 'success');
    }
  } catch (error) {
    pushMessage(error.message || '加载站点数据失败', 'error');
  } finally {
    loading.value = false;
  }
}

async function refreshData() {
  loading.value = true;
  try {
    const result = await pluginRequest(props.api, '/refresh', { method: 'POST', body: {} });
    if (!result?.success) {
      throw new Error(result?.message || '刷新失败')
    }
    const data = result.data || {};
    Object.assign(summary, data.summary || {});
    alerts.value = data.alerts || [];
    sites.value = data.sites || [];
    yearGroups.value = data.year_groups || [];
    fetchedAt.value = data.fetched_at || '';
    warning.value = data.warning || '';
    pushMessage(result.message || '刷新成功', 'success');
  } catch (error) {
    pushMessage(error.message || '刷新失败', 'error');
  } finally {
    loading.value = false;
  }
}

computed(() => {
  return sites.value.filter(site => site.anniversary_flag === 'yes' && site.status !== 'closed')
});

const noticeSections = computed(() => buildNoticeSections(alerts.value));

const yearOptions = computed(() => {
  const years = Array.from(new Set(yearGroups.value.map(item => item.year)));
  const hasUnknownYear = sites.value.some(site => !site.year || site.year === '0000');
  if (hasUnknownYear && !years.includes('0000')) {
    years.push('0000');
  }
  return ['全部', ...years]
});

const yearMenuOpen = ref(false);
const yearMenuRef = ref(null);
const mpStatusMenuOpen = ref(false);
const mpStatusMenuRef = ref(null);
const rootRef = ref(null);
let scrollTarget = null;
let restoreScrollTargetPosition = '';

const filteredSites = computed(() => {
  return sites.value.filter(site => {
    if (filters.keyword) {
      const keywords = buildSiteKeywords(site);
      if (!keywords.includes(filters.keyword.trim().toLowerCase())) {
        return false
      }
    }
    if (filters.year !== '全部' && site.year !== filters.year) {
      return false
    }
    if (filters.mpStatus !== '全部') {
      const status = site.mp_status || 'unsupported';
      if (status !== filters.mpStatus) {
        return false
      }
    }
    if (filters.status !== '全部') {
      const label = getStatusMeta(site.status).label;
      if (label !== filters.status) {
        return false
      }
    }
    if (filters.type !== '全部' && site.site_type !== filters.type) {
      return false
    }
    if (filters.anniversaryOnly && !(site.anniversary_flag === 'yes' && site.status !== 'closed')) {
      return false
    }
    return true
  })
});

const groupedSites = computed(() => {
  const groups = new Map();
  for (const site of filteredSites.value) {
    if (!groups.has(site.year)) {
      groups.set(site.year, []);
    }
    groups.get(site.year).push(site);
  }
  return Array.from(groups.entries()).map(([year, items]) => ({ year, items }))
});

const collapsedYears = reactive({});

function isYearGroupCollapsed(year) {
  return !!collapsedYears[year]
}

function toggleYearGroup(year) {
  collapsedYears[year] = !collapsedYears[year];
}

function toggleYearMenu() {
  yearMenuOpen.value = !yearMenuOpen.value;
}

function selectYear(year) {
  filters.year = year;
  yearMenuOpen.value = false;
}

function mpStatusOptionLabel(value) {
  const option = mpFilterOptions.find(item => item.value === value);
  return option ? option.label : '全部'
}

function getAnniversaryDisplayText(text) {
  const raw = `${text || ''}`.trim();
  if (!raw) {
    return ''
  }
  if (raw.includes('今天站庆')) {
    return '🎉 今天站庆！'
  }
  return raw.replace(/^emoji\s*站庆\s*/i, '').trim()
}

function isTodayAnniversaryText(text) {
  return getAnniversaryDisplayText(text) === '🎉 今天站庆！'
}

function toggleMpStatusMenu() {
  mpStatusMenuOpen.value = !mpStatusMenuOpen.value;
}

function selectMpStatus(value) {
  filters.mpStatus = value;
  mpStatusMenuOpen.value = false;
}

function handleDocumentClick(event) {
  if (!yearMenuRef.value?.contains(event.target)) {
    yearMenuOpen.value = false;
  }
  if (!mpStatusMenuRef.value?.contains(event.target)) {
    mpStatusMenuOpen.value = false;
  }
}

function findScrollParent(element) {
  let current = element?.parentElement;
  while (current) {
    const style = window.getComputedStyle(current);
    const overflowY = style.overflowY;
    if ((overflowY === 'auto' || overflowY === 'scroll') && current.scrollHeight > current.clientHeight) {
      return current
    }
    current = current.parentElement;
  }
  return window
}

function handleScroll() {
  const scrollTop = scrollTarget === window
    ? window.scrollY || document.documentElement.scrollTop || document.body.scrollTop || 0
    : scrollTarget?.scrollTop || 0;
  showBackToTop.value = scrollTop > 10;

  if (scrollTarget && scrollTarget !== window) {
    const rect = scrollTarget.getBoundingClientRect();
    const rightInset = Math.max(window.innerWidth - rect.right, 0) + 24;
    const bottomInset = Math.max(window.innerHeight - rect.bottom, 0) + 24;
    backTopStyle.value = {
      right: `${rightInset}px`,
      bottom: `${bottomInset}px`,
    };
  } else {
    backTopStyle.value = {
      right: '24px',
      bottom: '24px',
    };
  }
}

function scrollToTop() {
  if (scrollTarget === window) {
    window.scrollTo({ top: 0, behavior: 'smooth' });
    return
  }
  scrollTarget?.scrollTo({ top: 0, behavior: 'smooth' });
}

function formatYearLabel(year) {
  if (!year || year === '0000') {
    return '未知'
  }
  return year
}

function isUnknownYear(year) {
  return formatYearLabel(year) === '未知'
}

function yearOptionLabel(year) {
  if (year === '全部') {
    return '全部年份'
  }
  return isUnknownYear(year) ? '未知年份' : `${formatYearLabel(year)} 年`
}

function statusMeta(site) {
  return getStatusMeta(site.status)
}

function mpStatusMeta(site) {
  return getMpStatusMeta(site.mp_status)
}

function siteCelebrationKey(year, site) {
  return `${year || site.year || '0000'}-${site.name || site.url || 'site'}`
}

const activeAnniversaryCardKeys = computed(() => {
  const keys = [];
  for (const group of groupedSites.value) {
    if (isYearGroupCollapsed(group.year)) {
      continue
    }
    for (const site of group.items) {
      if (isTodayAnniversaryText(site.anniversary_text)) {
        keys.push(siteCelebrationKey(group.year, site));
      }
    }
  }
  return keys
});

function setCelebrationCanvasRef(cardKey, element) {
  if (element) {
    celebrationCanvasRefs.set(cardKey, element);
    return
  }
  celebrationCanvasRefs.delete(cardKey);
}

function isCompactViewport() {
  return typeof window !== 'undefined' && window.innerWidth <= 768
}

function celebrationLoopDelay() {
  return isCompactViewport() ? 3600 : 2800
}

async function ensureCelebrationConfettiFactory() {
  if (celebrationConfettiFactory) {
    return celebrationConfettiFactory
  }
  if (!celebrationConfettiLoader) {
    celebrationConfettiLoader = __vitePreload(() => import('./confetti.module-1bd81bb7.js'),true?[]:void 0)
      .then((module) => {
        celebrationConfettiFactory = module.default || module;
        return celebrationConfettiFactory
      })
      .catch((error) => {
        console.error('[savept] 加载 canvas-confetti 失败', error);
        celebrationConfettiLoader = null;
        return null
      });
  }
  return celebrationConfettiLoader
}

async function ensureCelebrationConfettiInstance(cardKey) {
  if (celebrationConfettiInstances.has(cardKey)) {
    return celebrationConfettiInstances.get(cardKey)
  }
  const canvas = celebrationCanvasRefs.get(cardKey);
  if (!canvas || prefersReducedMotion.value) {
    return null
  }
  const factory = await ensureCelebrationConfettiFactory();
  if (!factory || !celebrationCanvasRefs.has(cardKey)) {
    return null
  }
  const instance = factory.create(canvas, {
    resize: true,
    useWorker: false,
  });
  celebrationConfettiInstances.set(cardKey, instance);
  return instance
}

function celebrationBurstOptions(side = 'left') {
  const compact = isCompactViewport();
  return {
    particleCount: compact ? (side === 'left' ? 10 : 8) : (side === 'left' ? 18 : 14),
    angle: side === 'left' ? 52 : 128,
    spread: compact ? 44 : 60,
    startVelocity: compact ? 18 : 24,
    scalar: compact ? 0.72 : 0.92,
    ticks: compact ? 70 : 95,
    gravity: compact ? 1.08 : 0.96,
    drift: side === 'left' ? 0.08 : -0.08,
    origin: side === 'left'
      ? { x: compact ? 0.08 : 0.06, y: compact ? 0.94 : 0.92 }
      : { x: compact ? 0.92 : 0.94, y: compact ? 0.94 : 0.92 },
    colors: ['#f59e0b', '#facc15', '#fb7185', '#22c55e', '#38bdf8'],
  }
}

function fireCelebrationBurst(confetti) {
  confetti(celebrationBurstOptions('left'));
  confetti(celebrationBurstOptions('right'));
}

function stopCelebrationLoop(cardKey) {
  const timer = celebrationConfettiTimers.get(cardKey);
  if (timer) {
    clearTimeout(timer);
  }
  celebrationConfettiTimers.delete(cardKey);
}

function resetCelebrationConfetti(cardKey) {
  stopCelebrationLoop(cardKey);
  const instance = celebrationConfettiInstances.get(cardKey);
  instance?.reset?.();
}

function destroyCelebrationConfetti(cardKey) {
  resetCelebrationConfetti(cardKey);
  celebrationConfettiInstances.delete(cardKey);
}

function queueCelebrationLoop(cardKey) {
  stopCelebrationLoop(cardKey);
  const timer = window.setTimeout(() => {
    startCelebrationLoop(cardKey);
  }, celebrationLoopDelay());
  celebrationConfettiTimers.set(cardKey, timer);
}

async function startCelebrationLoop(cardKey) {
  stopCelebrationLoop(cardKey);
  if (prefersReducedMotion.value || document.visibilityState === 'hidden') {
    return
  }
  const confetti = await ensureCelebrationConfettiInstance(cardKey);
  if (!confetti || !celebrationCanvasRefs.has(cardKey)) {
    return
  }
  fireCelebrationBurst(confetti);
  if (!prefersReducedMotion.value && document.visibilityState !== 'hidden') {
    queueCelebrationLoop(cardKey);
  }
}

function syncCelebrationConfetti() {
  if (typeof window === 'undefined') {
    return
  }
  const activeKeys = new Set(activeAnniversaryCardKeys.value.filter(cardKey => celebrationCanvasRefs.has(cardKey)));

  for (const cardKey of celebrationConfettiTimers.keys()) {
    if (!activeKeys.has(cardKey)) {
      stopCelebrationLoop(cardKey);
    }
  }

  for (const cardKey of celebrationConfettiInstances.keys()) {
    if (!activeKeys.has(cardKey)) {
      destroyCelebrationConfetti(cardKey);
    }
  }

  if (prefersReducedMotion.value || document.visibilityState === 'hidden') {
    for (const cardKey of activeKeys) {
      resetCelebrationConfetti(cardKey);
    }
    return
  }

  for (const cardKey of activeKeys) {
    if (!celebrationConfettiTimers.has(cardKey)) {
      startCelebrationLoop(cardKey);
    }
  }
}

function handleReducedMotionChange(event) {
  prefersReducedMotion.value = !!event.matches;
  syncCelebrationConfetti();
}

function handleVisibilityChange() {
  syncCelebrationConfetti();
}

watch(activeAnniversaryCardKeys, async () => {
  await nextTick();
  syncCelebrationConfetti();
}, { flush: 'post' });

watch(groupedSites, async () => {
  await nextTick();
  syncCelebrationConfetti();
}, { flush: 'post' });

onMounted(() => {
  document.addEventListener('click', handleDocumentClick);
  scrollTarget = findScrollParent(rootRef.value);
  if (scrollTarget !== window && scrollTarget) {
    restoreScrollTargetPosition = scrollTarget.style.position || '';
    const computedPosition = window.getComputedStyle(scrollTarget).position;
    if (!computedPosition || computedPosition === 'static') {
      scrollTarget.style.position = 'relative';
    }
  }

  reducedMotionMediaQuery = window.matchMedia('(prefers-reduced-motion: reduce)');
  prefersReducedMotion.value = reducedMotionMediaQuery.matches;
  if (reducedMotionMediaQuery.addEventListener) {
    reducedMotionMediaQuery.addEventListener('change', handleReducedMotionChange);
  } else {
    reducedMotionMediaQuery.addListener(handleReducedMotionChange);
  }
  document.addEventListener('visibilitychange', handleVisibilityChange);

  window.addEventListener('resize', handleScroll, { passive: true });
  window.addEventListener('resize', syncCelebrationConfetti, { passive: true });
  if (scrollTarget === window) {
    window.addEventListener('scroll', handleScroll, { passive: true });
  } else {
    scrollTarget?.addEventListener('scroll', handleScroll, { passive: true });
  }
  handleScroll();
  loadData();
});

onBeforeUnmount(() => {
  clearMessageTimer();
  document.removeEventListener('click', handleDocumentClick);
  document.removeEventListener('visibilitychange', handleVisibilityChange);
  if (reducedMotionMediaQuery) {
    if (reducedMotionMediaQuery.removeEventListener) {
      reducedMotionMediaQuery.removeEventListener('change', handleReducedMotionChange);
    } else {
      reducedMotionMediaQuery.removeListener(handleReducedMotionChange);
    }
  }
  for (const cardKey of celebrationConfettiTimers.keys()) {
    stopCelebrationLoop(cardKey);
  }
  for (const cardKey of celebrationConfettiInstances.keys()) {
    destroyCelebrationConfetti(cardKey);
  }
  celebrationCanvasRefs.clear();
  window.removeEventListener('resize', handleScroll);
  window.removeEventListener('resize', syncCelebrationConfetti);
  if (scrollTarget === window) {
    window.removeEventListener('scroll', handleScroll);
  } else {
    scrollTarget?.removeEventListener('scroll', handleScroll);
    if (scrollTarget && restoreScrollTargetPosition !== undefined) {
      scrollTarget.style.position = restoreScrollTargetPosition;
    }
  }
});

return (_ctx, _cache) => {
  const _component_v_icon = _resolveComponent("v-icon");
  const _component_v_progress_circular = _resolveComponent("v-progress-circular");

  return (_openBlock(), _createElementBlock("div", {
    ref_key: "rootRef",
    ref: rootRef,
    class: "spt-root"
  }, [
    _createElementVNode("div", _hoisted_1, [
      _createElementVNode("div", _hoisted_2, [
        _createElementVNode("div", _hoisted_3, [
          _createElementVNode("div", _hoisted_4, [
            _createVNode(_component_v_icon, {
              icon: "mdi-heart-pulse",
              size: "22"
            })
          ]),
          _cache[5] || (_cache[5] = _createElementVNode("div", null, [
            _createElementVNode("h1", { class: "spt-header__title" }, "PT 监护室"),
            _createElementVNode("p", { class: "spt-header__desc" }, "站点运行状态实时监护")
          ], -1))
        ]),
        _createElementVNode("div", _hoisted_5, [
          _createElementVNode("div", _hoisted_6, [
            _createElementVNode("span", _hoisted_7, _toDisplayString(summary.total), 1),
            _cache[6] || (_cache[6] = _createElementVNode("span", { class: "spt-vital__label" }, "监护中", -1))
          ]),
          _cache[12] || (_cache[12] = _createElementVNode("div", { class: "spt-vital__divider" }, null, -1)),
          _createElementVNode("div", _hoisted_8, [
            _createElementVNode("span", _hoisted_9, _toDisplayString(summary.healthy), 1),
            _cache[7] || (_cache[7] = _createElementVNode("span", { class: "spt-vital__label" }, "健康", -1))
          ]),
          _cache[13] || (_cache[13] = _createElementVNode("div", { class: "spt-vital__divider" }, null, -1)),
          _createElementVNode("div", _hoisted_10, [
            _createElementVNode("span", _hoisted_11, _toDisplayString(summary.mp_owned), 1),
            _cache[8] || (_cache[8] = _createElementVNode("span", { class: "spt-vital__label" }, "已拥有", -1))
          ]),
          _cache[14] || (_cache[14] = _createElementVNode("div", { class: "spt-vital__divider" }, null, -1)),
          _createElementVNode("div", _hoisted_12, [
            _createElementVNode("span", _hoisted_13, _toDisplayString(summary.critical), 1),
            _cache[9] || (_cache[9] = _createElementVNode("span", { class: "spt-vital__label" }, "病危", -1))
          ]),
          _cache[15] || (_cache[15] = _createElementVNode("div", { class: "spt-vital__divider" }, null, -1)),
          _createElementVNode("div", _hoisted_14, [
            _createElementVNode("span", _hoisted_15, _toDisplayString(summary.closed), 1),
            _cache[10] || (_cache[10] = _createElementVNode("span", { class: "spt-vital__label" }, "已关站", -1))
          ]),
          _cache[16] || (_cache[16] = _createElementVNode("div", { class: "spt-vital__divider" }, null, -1)),
          _createElementVNode("div", _hoisted_16, [
            _createElementVNode("span", _hoisted_17, _toDisplayString(summary.today_anniv), 1),
            _cache[11] || (_cache[11] = _createElementVNode("span", { class: "spt-vital__label" }, "站庆", -1))
          ])
        ]),
        _createElementVNode("div", _hoisted_18, [
          _createElementVNode("span", _hoisted_19, [
            _createVNode(_component_v_icon, {
              icon: "mdi-web",
              size: "14"
            }),
            _createTextVNode(" " + _toDisplayString(summary.internal) + "/" + _toDisplayString(summary.external) + " 内外站 ", 1)
          ]),
          _createElementVNode("button", {
            class: "spt-refresh-btn",
            onClick: refreshData,
            disabled: loading.value
          }, [
            (loading.value)
              ? (_openBlock(), _createBlock(_component_v_progress_circular, {
                  key: 0,
                  size: "16",
                  width: "2",
                  indeterminate: "",
                  color: "inherit"
                }))
              : (_openBlock(), _createBlock(_component_v_icon, {
                  key: 1,
                  icon: "mdi-refresh",
                  size: "18"
                })),
            _cache[17] || (_cache[17] = _createElementVNode("span", null, "刷新数据", -1))
          ], 8, _hoisted_20)
        ])
      ]),
      _createElementVNode("div", _hoisted_21, [
        _createElementVNode("div", _hoisted_22, [
          _createVNode(_component_v_icon, {
            icon: "mdi-magnify",
            size: "18",
            class: "spt-filters__search-icon"
          }),
          _withDirectives(_createElementVNode("input", {
            "onUpdate:modelValue": _cache[0] || (_cache[0] = $event => ((filters.keyword) = $event)),
            type: "text",
            placeholder: "搜索站点名称...",
            class: "spt-filters__input"
          }, null, 512), [
            [_vModelText, filters.keyword]
          ]),
          (filters.keyword)
            ? (_openBlock(), _createElementBlock("button", {
                key: 0,
                class: "spt-filters__clear",
                onClick: _cache[1] || (_cache[1] = $event => (filters.keyword = ''))
              }, [
                _createVNode(_component_v_icon, {
                  icon: "mdi-close-circle",
                  size: "16"
                })
              ]))
            : _createCommentVNode("", true)
        ]),
        _cache[20] || (_cache[20] = _createElementVNode("div", { class: "spt-filters__divider" }, null, -1)),
        _createElementVNode("div", {
          class: "spt-filters__group spt-year-select",
          ref_key: "yearMenuRef",
          ref: yearMenuRef
        }, [
          _createElementVNode("button", {
            class: _normalizeClass(["spt-filters__select-btn", { 'spt-filters__select-btn--open': yearMenuOpen.value }]),
            onClick: _withModifiers(toggleYearMenu, ["stop"])
          }, [
            _createVNode(_component_v_icon, {
              icon: "mdi-calendar",
              size: "16",
              class: "spt-filters__group-icon"
            }),
            _createElementVNode("span", _hoisted_23, _toDisplayString(yearOptionLabel(filters.year)), 1),
            _createVNode(_component_v_icon, {
              icon: "mdi-chevron-down",
              size: "16",
              class: _normalizeClass(["spt-filters__select-chevron", { 'spt-filters__select-chevron--open': yearMenuOpen.value }])
            }, null, 8, ["class"])
          ], 2),
          (yearMenuOpen.value)
            ? (_openBlock(), _createElementBlock("div", _hoisted_24, [
                (_openBlock(true), _createElementBlock(_Fragment, null, _renderList(yearOptions.value, (y) => {
                  return (_openBlock(), _createElementBlock("button", {
                    key: y,
                    class: _normalizeClass(["spt-filters__dropdown-item", { 'spt-filters__dropdown-item--active': filters.year === y }]),
                    onClick: _withModifiers($event => (selectYear(y)), ["stop"])
                  }, _toDisplayString(yearOptionLabel(y)), 11, _hoisted_25))
                }), 128))
              ]))
            : _createCommentVNode("", true)
        ], 512),
        _cache[21] || (_cache[21] = _createElementVNode("div", { class: "spt-filters__divider" }, null, -1)),
        _createElementVNode("div", {
          class: "spt-filters__group spt-year-select",
          ref_key: "mpStatusMenuRef",
          ref: mpStatusMenuRef
        }, [
          _createElementVNode("button", {
            class: _normalizeClass(["spt-filters__select-btn", { 'spt-filters__select-btn--open': mpStatusMenuOpen.value }]),
            onClick: _withModifiers(toggleMpStatusMenu, ["stop"])
          }, [
            _createVNode(_component_v_icon, {
              icon: "mdi-check-decagram",
              size: "16",
              class: "spt-filters__group-icon"
            }),
            _createElementVNode("span", _hoisted_26, _toDisplayString(mpStatusOptionLabel(filters.mpStatus)), 1),
            _createVNode(_component_v_icon, {
              icon: "mdi-chevron-down",
              size: "16",
              class: _normalizeClass(["spt-filters__select-chevron", { 'spt-filters__select-chevron--open': mpStatusMenuOpen.value }])
            }, null, 8, ["class"])
          ], 2),
          (mpStatusMenuOpen.value)
            ? (_openBlock(), _createElementBlock("div", _hoisted_27, [
                (_openBlock(), _createElementBlock(_Fragment, null, _renderList(mpFilterOptions, (opt) => {
                  return _createElementVNode("button", {
                    key: opt.value,
                    class: _normalizeClass(["spt-filters__dropdown-item", { 'spt-filters__dropdown-item--active': filters.mpStatus === opt.value }]),
                    onClick: _withModifiers($event => (selectMpStatus(opt.value)), ["stop"])
                  }, _toDisplayString(mpStatusOptionLabel(opt.value)), 11, _hoisted_28)
                }), 64))
              ]))
            : _createCommentVNode("", true)
        ], 512),
        _cache[22] || (_cache[22] = _createElementVNode("div", { class: "spt-filters__divider" }, null, -1)),
        _createElementVNode("div", _hoisted_29, [
          (_openBlock(), _createElementBlock(_Fragment, null, _renderList(statusOptions, (opt) => {
            return _createElementVNode("button", {
              key: opt.value,
              class: _normalizeClass(["spt-pill", {
              'spt-pill--active': filters.status === opt.value,
              'spt-pill--healthy': filters.status === '健康' && opt.value === '健康',
              'spt-pill--critical': filters.status === '病危' && opt.value === '病危',
              'spt-pill--closed': filters.status === '死亡' && opt.value === '死亡',
            }]),
              onClick: $event => (filters.status = opt.value)
            }, _toDisplayString(opt.label), 11, _hoisted_30)
          }), 64))
        ]),
        _cache[23] || (_cache[23] = _createElementVNode("div", { class: "spt-filters__divider" }, null, -1)),
        _createElementVNode("div", _hoisted_31, [
          (_openBlock(), _createElementBlock(_Fragment, null, _renderList(typeOptions, (opt) => {
            return _createElementVNode("button", {
              key: opt.value,
              class: _normalizeClass(["spt-pill", { 'spt-pill--active': filters.type === opt.value }]),
              onClick: $event => (filters.type = opt.value)
            }, _toDisplayString(opt.label), 11, _hoisted_32)
          }), 64)),
          _createElementVNode("button", {
            class: _normalizeClass(["spt-pill spt-pill--anniv-toggle", { 'spt-pill--anniv-active': filters.anniversaryOnly }]),
            onClick: _cache[2] || (_cache[2] = $event => (filters.anniversaryOnly = !filters.anniversaryOnly))
          }, [
            _createVNode(_component_v_icon, {
              icon: "mdi-party-popper",
              size: "14"
            }),
            _cache[18] || (_cache[18] = _createTextVNode(" 近期站庆 ", -1))
          ], 2)
        ]),
        _cache[24] || (_cache[24] = _createElementVNode("div", { class: "spt-filters__spacer" }, null, -1)),
        _createElementVNode("div", _hoisted_33, [
          (fetchedAt.value)
            ? (_openBlock(), _createElementBlock("span", _hoisted_34, [
                _createVNode(_component_v_icon, {
                  icon: "mdi-clock-outline",
                  size: "14"
                }),
                _createTextVNode(" " + _toDisplayString(fetchedAt.value), 1)
              ]))
            : _createCommentVNode("", true),
          _createElementVNode("span", _hoisted_35, [
            _cache[19] || (_cache[19] = _createTextVNode(" 显示 ", -1)),
            _createElementVNode("b", null, _toDisplayString(filteredSites.value.length), 1),
            _createTextVNode(" / " + _toDisplayString(sites.value.length) + " 个站点 ", 1)
          ])
        ])
      ])
    ]),
    _createElementVNode("div", _hoisted_36, [
      (_openBlock(true), _createElementBlock(_Fragment, null, _renderList(noticeSections.value, (section) => {
        return (_openBlock(), _createElementBlock("div", {
          key: section.key,
          class: _normalizeClass(["spt-notice-card", `spt-notice-card--${section.key}`])
        }, [
          _createElementVNode("div", _hoisted_37, _toDisplayString(section.title), 1),
          (section.items.length)
            ? (_openBlock(), _createElementBlock("div", _hoisted_38, [
                (_openBlock(true), _createElementBlock(_Fragment, null, _renderList(section.items, (item, index) => {
                  return (_openBlock(), _createElementBlock("div", {
                    key: `${section.key}-${index}`,
                    class: "spt-notice-card__item"
                  }, [
                    (_openBlock(true), _createElementBlock(_Fragment, null, _renderList(_unref(tokenizeNoticeText)(item, sites.value), (token, tokenIndex) => {
                      return (_openBlock(), _createElementBlock(_Fragment, {
                        key: `${section.key}-${index}-${tokenIndex}`
                      }, [
                        (token.type === 'site')
                          ? (_openBlock(), _createElementBlock("span", {
                              key: 0,
                              class: _normalizeClass(["spt-notice-tag", `spt-notice-tag--${section.key}`])
                            }, _toDisplayString(token.text), 3))
                          : (_openBlock(), _createElementBlock("span", _hoisted_39, _toDisplayString(token.text), 1))
                      ], 64))
                    }), 128))
                  ]))
                }), 128))
              ]))
            : (_openBlock(), _createElementBlock("div", _hoisted_40, "暂无公告"))
        ], 2))
      }), 128))
    ]),
    _createVNode(_Transition, { name: "spt-slide" }, {
      default: _withCtx(() => [
        (message.show)
          ? (_openBlock(), _createElementBlock("div", {
              key: 0,
              class: _normalizeClass(["spt-toast", `spt-toast--${message.type}`])
            }, [
              _createVNode(_component_v_icon, {
                icon: message.type === 'success' ? 'mdi-check-circle' : message.type === 'error' ? 'mdi-alert-circle' : 'mdi-information',
                size: "18"
              }, null, 8, ["icon"]),
              _createElementVNode("span", null, _toDisplayString(message.text), 1),
              _createElementVNode("button", {
                class: "spt-toast__close",
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
    (warning.value)
      ? (_openBlock(), _createElementBlock("div", _hoisted_41, [
          _createVNode(_component_v_icon, {
            icon: "mdi-alert-outline",
            size: "18"
          }),
          _createElementVNode("span", null, _toDisplayString(warning.value), 1)
        ]))
      : _createCommentVNode("", true),
    (_openBlock(true), _createElementBlock(_Fragment, null, _renderList(groupedSites.value, (group) => {
      return (_openBlock(), _createElementBlock("div", {
        key: group.year,
        class: "spt-year-group"
      }, [
        _createElementVNode("div", _hoisted_42, [
          _createElementVNode("button", {
            type: "button",
            class: _normalizeClass(["spt-year-group__toggle", { 'spt-year-group__toggle--collapsed': isYearGroupCollapsed(group.year) }]),
            onClick: $event => (toggleYearGroup(group.year))
          }, [
            _createElementVNode("div", _hoisted_44, _toDisplayString(formatYearLabel(group.year)), 1),
            _createElementVNode("span", _hoisted_45, _toDisplayString(isUnknownYear(group.year) ? '年份建站' : '年建站'), 1),
            _createElementVNode("span", _hoisted_46, _toDisplayString(group.items.length) + " 个站点", 1)
          ], 10, _hoisted_43),
          _createElementVNode("button", {
            type: "button",
            class: _normalizeClass(["spt-year-group__chevron-btn", { 'spt-year-group__chevron-btn--collapsed': isYearGroupCollapsed(group.year) }]),
            onClick: $event => (toggleYearGroup(group.year)),
            "aria-label": isYearGroupCollapsed(group.year) ? `展开 ${formatYearLabel(group.year)} 年分组` : `收起 ${formatYearLabel(group.year)} 年分组`
          }, [
            _createVNode(_component_v_icon, {
              class: _normalizeClass(["spt-year-group__chevron", { 'spt-year-group__chevron--collapsed': isYearGroupCollapsed(group.year) }]),
              icon: "mdi-chevron-down",
              size: "18"
            }, null, 8, ["class"])
          ], 10, _hoisted_47)
        ]),
        _withDirectives(_createElementVNode("div", _hoisted_48, [
          (_openBlock(true), _createElementBlock(_Fragment, null, _renderList(group.items, (site) => {
            return (_openBlock(), _createElementBlock("a", {
              key: `${group.year}-${site.name}`,
              href: site.url,
              target: "_blank",
              rel: "noreferrer noopener",
              class: _normalizeClass(["spt-card", [`spt-card--${site.status || 'unknown'}`, { 'spt-card--anniversary-today': isTodayAnniversaryText(site.anniversary_text) }]])
            }, [
              (isTodayAnniversaryText(site.anniversary_text))
                ? (_openBlock(), _createElementBlock("div", _hoisted_50, [
                    _createElementVNode("canvas", {
                      ref_for: true,
                      ref: element => setCelebrationCanvasRef(siteCelebrationKey(group.year, site), element),
                      class: "spt-card__celebration-canvas"
                    }, null, 512),
                    _cache[25] || (_cache[25] = _createElementVNode("span", { class: "spt-card__spark spt-card__spark--one" }, null, -1)),
                    _cache[26] || (_cache[26] = _createElementVNode("span", { class: "spt-card__spark spt-card__spark--two" }, null, -1)),
                    _cache[27] || (_cache[27] = _createElementVNode("span", { class: "spt-card__spark spt-card__spark--three" }, null, -1)),
                    _cache[28] || (_cache[28] = _createElementVNode("span", { class: "spt-card__spark spt-card__spark--four" }, null, -1))
                  ]))
                : _createCommentVNode("", true),
              _createElementVNode("div", _hoisted_51, [
                _createElementVNode("div", _hoisted_52, [
                  _createElementVNode("div", _hoisted_53, [
                    _createElementVNode("span", _hoisted_54, _toDisplayString(site.site_type), 1),
                    (site.duration_text)
                      ? (_openBlock(), _createElementBlock("span", _hoisted_55, [
                          _createVNode(_component_v_icon, {
                            icon: "mdi-clock-fast",
                            size: "12"
                          }),
                          _createElementVNode("span", _hoisted_56, _toDisplayString(site.duration_text), 1)
                        ]))
                      : _createCommentVNode("", true),
                    (site.anniversary_text)
                      ? (_openBlock(), _createElementBlock("span", {
                          key: 1,
                          class: _normalizeClass(["spt-tag spt-tag--anniversary", { 'spt-tag--anniversary-today': isTodayAnniversaryText(site.anniversary_text) }])
                        }, [
                          (!isTodayAnniversaryText(site.anniversary_text))
                            ? (_openBlock(), _createBlock(_component_v_icon, {
                                key: 0,
                                icon: "mdi-party-popper",
                                size: "12"
                              }))
                            : _createCommentVNode("", true),
                          _createElementVNode("span", _hoisted_57, _toDisplayString(getAnniversaryDisplayText(site.anniversary_text)), 1)
                        ], 2))
                      : _createCommentVNode("", true)
                  ])
                ]),
                _createElementVNode("div", _hoisted_58, [
                  _createElementVNode("img", {
                    class: "spt-card__icon",
                    src: site.icon,
                    alt: site.name,
                    loading: "lazy"
                  }, null, 8, _hoisted_59),
                  _createElementVNode("div", _hoisted_60, [
                    _createElementVNode("div", _hoisted_61, [
                      _createElementVNode("span", {
                        class: "spt-card__name-dot",
                        style: _normalizeStyle({ backgroundColor: statusMeta(site).color })
                      }, null, 4),
                      _createElementVNode("div", _hoisted_62, _toDisplayString(site.name), 1)
                    ]),
                    _createElementVNode("div", _hoisted_63, [
                      _createTextVNode("开站 " + _toDisplayString(site.open_time || '未知'), 1),
                      (site.close_time && site.close_time !== '未知')
                        ? (_openBlock(), _createElementBlock(_Fragment, { key: 0 }, [
                            _createTextVNode(" · 关站 " + _toDisplayString(site.close_time), 1)
                          ], 64))
                        : _createCommentVNode("", true)
                    ]),
                    (site.mp_status || site.mp_site_name || site.mp_site_domain)
                      ? (_openBlock(), _createElementBlock("div", _hoisted_64, [
                          (site.mp_site_name || site.mp_site_domain)
                            ? (_openBlock(), _createElementBlock("span", _hoisted_65, [
                                _createElementVNode("span", null, _toDisplayString(site.mp_site_name || site.name), 1),
                                (site.mp_site_domain)
                                  ? (_openBlock(), _createElementBlock(_Fragment, { key: 0 }, [
                                      _createTextVNode(" · " + _toDisplayString(site.mp_site_domain), 1)
                                    ], 64))
                                  : _createCommentVNode("", true)
                              ]))
                            : _createCommentVNode("", true),
                          (site.mp_status)
                            ? (_openBlock(), _createElementBlock("span", {
                                key: 1,
                                class: _normalizeClass(["spt-tag spt-tag--mp", `spt-tag--mp-${mpStatusMeta(site).chipClass}`])
                              }, [
                                _createVNode(_component_v_icon, {
                                  icon: mpStatusMeta(site).icon,
                                  size: "12"
                                }, null, 8, ["icon"]),
                                _createTextVNode(" " + _toDisplayString(site.mp_status_text || mpStatusMeta(site).label), 1)
                              ], 2))
                            : _createCommentVNode("", true)
                        ]))
                      : _createCommentVNode("", true)
                  ])
                ])
              ]),
              (statusMeta(site).icon)
                ? (_openBlock(), _createElementBlock("div", {
                    key: 1,
                    class: "spt-card__status-icon",
                    style: _normalizeStyle({ color: statusMeta(site).color })
                  }, [
                    _createVNode(_component_v_icon, {
                      icon: statusMeta(site).icon,
                      size: "18"
                    }, null, 8, ["icon"])
                  ], 4))
                : _createCommentVNode("", true)
            ], 10, _hoisted_49))
          }), 128))
        ], 512), [
          [_vShow, !isYearGroupCollapsed(group.year)]
        ])
      ]))
    }), 128)),
    (!loading.value && filteredSites.value.length === 0)
      ? (_openBlock(), _createElementBlock("div", _hoisted_66, [
          _createVNode(_component_v_icon, {
            icon: "mdi-monitor-eye",
            size: "48",
            color: "grey-lighten-1"
          }),
          _cache[29] || (_cache[29] = _createElementVNode("p", null, "没有匹配的站点", -1)),
          _createElementVNode("button", {
            class: "spt-pill",
            onClick: _cache[4] || (_cache[4] = $event => (Object.assign(filters, { keyword: '', year: '全部', mpStatus: '全部', status: '全部', type: '全部', anniversaryOnly: false })))
          }, " 清除筛选 ")
        ]))
      : _createCommentVNode("", true),
    (_openBlock(), _createBlock(_Teleport, { to: "body" }, [
      _createVNode(_Transition, { name: "spt-fab" }, {
        default: _withCtx(() => [
          (showBackToTop.value)
            ? (_openBlock(), _createElementBlock("button", {
                key: 0,
                class: "spt-back-top",
                style: _normalizeStyle(backTopStyle.value),
                onClick: scrollToTop,
                "aria-label": "返回顶部"
              }, [
                _createVNode(_component_v_icon, {
                  icon: "mdi-chevron-up",
                  size: "20"
                })
              ], 4))
            : _createCommentVNode("", true)
        ]),
        _: 1
      })
    ]))
  ], 512))
}
}

};
const AppPage = /*#__PURE__*/_export_sfc(_sfc_main, [['__scopeId',"data-v-c7dff6f4"]]);

export { AppPage as default };
