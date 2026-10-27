<template>
  <main class="board-screen">
    <div id="particles-js" aria-hidden="true"></div>
    <div class="board-grid" aria-hidden="true"></div>
    <header class="board-header">
      <div class="header-side header-left">
        <router-link to="/news" class="board-back" aria-label="返回新闻库">← 新闻库</router-link>
        <span class="live-badge"><i></i>DATA ONLINE</span>
      </div>
      <div class="board-title">
        <span class="title-wing"></span>
        <div><h1>财经新闻智能分析大屏</h1><p>FINANCIAL NEWS INTELLIGENCE CENTER</p></div>
        <span class="title-wing right"></span>
      </div>
      <div class="header-side header-right">
        <div class="board-clock"><strong>{{ clock.time }}</strong><span>{{ clock.date }}</span></div>
        <button class="icon-button" type="button" @click="loadData" :disabled="loading" aria-label="刷新大屏数据" title="刷新数据"><span :class="{ rotating: loading }">↻</span></button>
        <button class="icon-button" type="button" @click="toggleFullscreen" aria-label="切换全屏" title="切换全屏">{{ isFullscreen ? '⊡' : '□' }}</button>
      </div>
    </header>

    <div v-if="error" class="board-error" role="alert">{{ error }} <button @click="loadData">重新连接</button></div>

    <section class="board-layout" :aria-busy="loading">
      <div class="board-column left-column">
        <article class="tech-panel category-panel">
          <PanelTitle index="01" title="行业新闻分布" subtitle="CATEGORY SHARE" />
          <div ref="categoryChart" class="chart chart-category" role="img" aria-label="行业新闻分布玫瑰图"></div>
        </article>
        <article class="tech-panel source-panel">
          <PanelTitle index="02" title="栏目来源排行" subtitle="SOURCE RANKING" />
          <div ref="sourceChart" class="chart chart-source" role="img" aria-label="新闻栏目来源排行条形图"></div>
        </article>
        <article class="tech-panel sentiment-panel">
          <PanelTitle index="03" title="情感倾向占比" subtitle="SENTIMENT RATIO" />
          <div ref="sentimentChart" class="chart chart-sentiment" role="img" aria-label="新闻情感倾向占比环形图"></div>
        </article>
      </div>

      <div class="board-column center-column">
        <section class="kpi-grid" aria-label="核心指标">
          <div class="kpi-item"><span>新闻样本 / TOTAL</span><strong>{{ formatNumber(data.overview.total) }}</strong><small>2024 全年收录</small></div>
          <div class="kpi-item"><span>行业分类 / CLASS</span><strong>{{ data.overview.categories }}<em>类</em></strong><small>财经行业标签</small></div>
          <div class="kpi-item accent"><span>积极报道 / POSITIVE</span><strong>{{ data.overview.positive_rate }}<em>%</em></strong><small>正向信号占比</small></div>
          <div class="kpi-item"><span>平均情感 / SCORE</span><strong>{{ signed(data.overview.average_score) }}</strong><small>区间 −1 至 +1</small></div>
        </section>
        <article class="tech-panel trend-panel">
          <PanelTitle index="04" title="全年情感演化趋势" subtitle="MONTHLY SENTIMENT EVOLUTION" />
          <div ref="trendChart" class="chart chart-trend" role="img" aria-label="全年月度情感趋势组合图"></div>
        </article>
        <article class="tech-panel industry-panel">
          <PanelTitle index="05" title="行业情感结构" subtitle="INDUSTRY SENTIMENT MATRIX" />
          <div ref="industryChart" class="chart chart-industry" role="img" aria-label="行业情感结构堆叠图"></div>
        </article>
      </div>

      <div class="board-column right-column">
        <article class="tech-panel keyword-panel">
          <PanelTitle index="06" title="新闻高频关键词" subtitle="KEYWORD FREQUENCY" />
          <div ref="keywordChart" class="chart chart-keyword" role="img" aria-label="新闻高频关键词气泡图"></div>
        </article>
        <article class="tech-panel latest-panel">
          <PanelTitle index="07" title="最新风险监测" subtitle="LATEST NEGATIVE SIGNALS" />
          <div class="signal-summary"><span><i></i>消极报道持续监测</span><strong>{{ data.overview.negative_count }} <small>篇</small></strong></div>
          <div class="latest-list">
            <button v-for="(news, index) in negativeLatest" :key="news.id" class="latest-item" @click="selectedId = news.id">
              <span class="news-index">{{ String(index + 1).padStart(2, '0') }}</span>
              <span class="latest-content"><strong>{{ news.title }}</strong><small>{{ news.published_at }} · {{ news.category }} · {{ news.source }}</small></span>
              <span class="latest-score">{{ signed(news.sentiment_score) }}</span>
            </button>
          </div>
        </article>
      </div>
    </section>

    <footer class="board-footer"><span>DATA SOURCE · THE PAPER / USER DATASET</span><span>规则辅助分析 · 仅供研究，不构成投资建议</span><span>LAST SYNC · {{ lastSync }}</span></footer>
    <NewsDetail v-if="selectedId" :news-id="selectedId" @close="selectedId = null" />
  </main>
</template>

<script>
import 'particles.js'
import NewsDetail from '../components/NewsDetail.vue'
import PanelTitle from '../components/PanelTitle.vue'
import { newsApi } from '../api'
import echarts, { sentimentColors } from '../plugins/echarts'

const emptyData = () => ({
  overview: { total: 0, categories: 0, positive_rate: 0, negative_count: 0, average_score: 0 },
  trend: { months: [], positive: [], neutral: [], negative: [], score: [] },
  category_sentiment: [], sources: [], keywords: [], latest: [],
})

export default {
  name: 'BoardView',
  components: { NewsDetail, PanelTitle },
  data() {
    return {
      data: emptyData(), loading: false, error: '', charts: [], selectedId: null,
      clock: { time: '--:--:--', date: '----年--月--日' }, lastSync: '--:--:--', isFullscreen: false,
    }
  },
  computed: {
    negativeLatest() { return this.data.latest.filter(item => item.sentiment === '消极').slice(0, 6) },
  },
  methods: {
    formatNumber(value) { return Number(value || 0).toLocaleString('zh-CN') },
    signed(value) { const number = Number(value || 0); return `${number > 0 ? '+' : ''}${number.toFixed(3)}` },
    updateClock() {
      const now = new Date()
      this.clock = {
        time: now.toLocaleTimeString('zh-CN', { hour12: false }),
        date: now.toLocaleDateString('zh-CN', { year: 'numeric', month: '2-digit', day: '2-digit', weekday: 'short' }),
      }
    },
    async loadData() {
      this.loading = true
      this.error = ''
      try {
        this.data = await newsApi.board()
        this.lastSync = new Date().toLocaleTimeString('zh-CN', { hour12: false })
        this.$nextTick(this.renderCharts)
      } catch (error) { this.error = error.message } finally { this.loading = false }
    },
    createChart(ref) {
      if (this.$refs[ref] && !echarts.getInstanceByDom(this.$refs[ref])) {
        // 用户指定：ECharts 5.4 直接 init，并显式使用 macarons 主题。
        const chart = echarts.init(this.$refs[ref], 'macarons', { renderer: 'canvas' })
        this.charts.push(chart)
      }
      return echarts.getInstanceByDom(this.$refs[ref])
    },
    renderCharts() {
      if (!this.$refs.categoryChart) return
      this.renderCategory()
      this.renderSources()
      this.renderSentiment()
      this.renderTrend()
      this.renderIndustry()
      this.renderKeywords()
      this.resizeCharts()
    },
    baseTooltip() { return { backgroundColor: 'rgba(4,13,23,.96)', borderColor: '#28516a', textStyle: { color: '#dff7ff', fontSize: 12 } } },
    renderCategory() {
      const items = this.data.category_sentiment.map(item => ({ name: item.category, value: item.total }))
      this.createChart('categoryChart').setOption({
        color: ['#2ec7c9', '#5ab1ef', '#ffb980', '#b6a2de', '#34d399', '#d87a80', '#e5cf0d', '#97b552', '#95706d', '#dc69aa', '#8d98b3'],
        tooltip: { ...this.baseTooltip(), trigger: 'item', formatter: '{b}<br/>{c} 篇 · {d}%' },
        legend: { type: 'scroll', orient: 'vertical', right: 4, top: 'center', itemWidth: 7, itemHeight: 7, itemGap: 8, textStyle: { color: '#91a9bd', fontSize: 10 }, pageIconColor: '#2ec7c9', pageTextStyle: { color: '#91a9bd' } },
        series: [{ type: 'pie', radius: ['44%', '70%'], center: ['35%', '51%'], minAngle: 3, avoidLabelOverlap: true, itemStyle: { borderColor: '#07111f', borderWidth: 2 }, label: { show: false }, emphasis: { label: { show: true, color: '#e4f7ff', fontSize: 12, formatter: '{b}\n{d}%' }, scaleSize: 6 }, data: items }],
      }, true)
    },
    renderSources() {
      const items = [...this.data.sources].slice(0, 6).reverse()
      this.createChart('sourceChart').setOption({
        tooltip: { ...this.baseTooltip(), trigger: 'axis', axisPointer: { type: 'shadow' } },
        grid: { left: 78, right: 30, top: 12, bottom: 22 },
        xAxis: { type: 'value', axisLabel: { color: '#66849b', fontSize: 9 }, splitLine: { lineStyle: { color: '#14293b', type: 'dashed' } } },
        yAxis: { type: 'category', data: items.map(d => d.name), axisTick: { show: false }, axisLine: { show: false }, axisLabel: { color: '#a1b8ca', fontSize: 10, width: 68, overflow: 'truncate' } },
        series: [{ type: 'bar', data: items.map(d => d.value), barWidth: 8, showBackground: true, backgroundStyle: { color: 'rgba(50,86,108,.18)' }, itemStyle: { color: new echarts.graphic.LinearGradient(0, 0, 1, 0, [{ offset: 0, color: '#176478' }, { offset: 1, color: '#2ec7c9' }]) }, label: { show: true, position: 'right', color: '#77dbe2', font: '10px monospace' } }],
      }, true)
    },
    renderSentiment() {
      const counts = { 积极: 0, 中性: 0, 消极: 0 }
      this.data.category_sentiment.forEach(item => { counts.积极 += item.positive; counts.中性 += item.neutral; counts.消极 += item.negative })
      this.createChart('sentimentChart').setOption({
        color: [sentimentColors.积极, sentimentColors.中性, sentimentColors.消极],
        tooltip: { ...this.baseTooltip(), trigger: 'item', formatter: '{b}：{c} 篇（{d}%）' },
        legend: { bottom: 0, left: 'center', itemWidth: 8, itemHeight: 8, itemGap: 18, textStyle: { color: '#9db3c4', fontSize: 10 } },
        title: { text: `${this.data.overview.positive_rate}%`, subtext: '积极报道', left: 'center', top: '34%', textStyle: { color: '#dffbff', fontSize: 24, fontFamily: 'monospace' }, subtextStyle: { color: '#6f91a8', fontSize: 10 } },
        series: [{ type: 'pie', radius: ['56%', '72%'], center: ['50%', '43%'], startAngle: 110, label: { show: false }, itemStyle: { borderColor: '#07111f', borderWidth: 3 }, data: Object.keys(counts).map(name => ({ name, value: counts[name] })) }],
      }, true)
    },
    renderTrend() {
      const trend = this.data.trend
      this.createChart('trendChart').setOption({
        color: [sentimentColors.积极, sentimentColors.中性, sentimentColors.消极, '#ffb980'],
        tooltip: { ...this.baseTooltip(), trigger: 'axis', axisPointer: { type: 'cross', lineStyle: { color: '#2ec7c9' } } },
        legend: { top: 0, right: 8, itemWidth: 10, itemHeight: 6, textStyle: { color: '#8fa9bd', fontSize: 10 }, data: ['积极', '中性', '消极', '平均得分'] },
        grid: { left: 44, right: 48, top: 38, bottom: 28 },
        xAxis: { type: 'category', data: trend.months.map(m => `${Number(m.slice(5))}月`), axisTick: { show: false }, axisLine: { lineStyle: { color: '#29445a' } }, axisLabel: { color: '#7e9bb0', fontSize: 10 } },
        yAxis: [
          { type: 'value', axisLabel: { color: '#6f8ca2', fontSize: 9 }, splitLine: { lineStyle: { color: '#152b3e', type: 'dashed' } } },
          { type: 'value', min: -0.3, max: 0.5, axisLabel: { color: '#6f8ca2', fontSize: 9 }, splitLine: { show: false } },
        ],
        series: [
          { name: '积极', type: 'bar', stack: 'total', data: trend.positive, barMaxWidth: 22 },
          { name: '中性', type: 'bar', stack: 'total', data: trend.neutral, barMaxWidth: 22 },
          { name: '消极', type: 'bar', stack: 'total', data: trend.negative, barMaxWidth: 22 },
          { name: '平均得分', type: 'line', yAxisIndex: 1, data: trend.score, smooth: .3, symbol: 'circle', symbolSize: 5, lineStyle: { width: 2, shadowColor: '#ffb980', shadowBlur: 8 }, areaStyle: { color: 'rgba(255,185,128,.05)' } },
        ],
      }, true)
    },
    renderIndustry() {
      const items = [...this.data.category_sentiment].reverse()
      this.createChart('industryChart').setOption({
        color: [sentimentColors.积极, sentimentColors.中性, sentimentColors.消极],
        tooltip: { ...this.baseTooltip(), trigger: 'axis', axisPointer: { type: 'shadow' }, formatter: params => `${params[0].name}<br/>${params.map(p => `${p.marker}${p.seriesName}：${p.data.count} 篇（${p.value}%）`).join('<br/>')}` },
        legend: { top: 0, right: 8, itemWidth: 9, itemHeight: 6, textStyle: { color: '#8fa9bd', fontSize: 10 } },
        grid: { left: 42, right: 14, top: 32, bottom: 28 },
        xAxis: { type: 'category', data: items.map(d => d.category), axisTick: { show: false }, axisLine: { lineStyle: { color: '#29445a' } }, axisLabel: { color: '#8fa9bd', fontSize: 9, interval: 0, rotate: items.length > 8 ? 28 : 0 } },
        yAxis: { type: 'value', max: 100, axisLabel: { color: '#6f8ca2', fontSize: 9, formatter: '{value}%' }, splitLine: { lineStyle: { color: '#152b3e', type: 'dashed' } } },
        series: [
          { name: '积极', type: 'bar', stack: 'total', data: items.map(d => ({ value: +(d.positive / d.total * 100).toFixed(2), count: d.positive })), barMaxWidth: 18 },
          { name: '中性', type: 'bar', stack: 'total', data: items.map(d => ({ value: +(d.neutral / d.total * 100).toFixed(2), count: d.neutral })), barMaxWidth: 18 },
          { name: '消极', type: 'bar', stack: 'total', data: items.map(d => ({ value: +(d.negative / d.total * 100).toFixed(2), count: d.negative })), barMaxWidth: 18 },
        ],
      }, true)
    },
    renderKeywords() {
      const values = this.data.keywords.slice(0, 24)
      const max = Math.max(...values.map(d => d.value), 1)
      this.createChart('keywordChart').setOption({
        tooltip: { ...this.baseTooltip(), formatter: params => `${params.data[2]}<br/>出现 ${params.data[1]} 篇` },
        grid: { left: 0, right: 0, top: 0, bottom: 0 },
        xAxis: { type: 'value', show: false, min: 0, max: 100 },
        yAxis: { type: 'value', show: false, min: 0, max: 100 },
        series: [{
          type: 'scatter', data: values.map((item, index) => [8 + (index * 37 % 84), 10 + (index * 53 % 76), item.name, item.value]),
          symbolSize: data => 22 + Math.sqrt(data[3] / max) * 38,
          label: { show: true, formatter: data => data.data[2], color: '#d6f5fa', fontSize: 10 },
          itemStyle: { color: params => ['rgba(46,199,201,.42)', 'rgba(90,177,239,.38)', 'rgba(255,185,128,.32)', 'rgba(182,162,222,.34)'][params.dataIndex % 4], borderColor: '#2ec7c9', borderWidth: 1, shadowBlur: 12, shadowColor: 'rgba(46,199,201,.24)' },
        }],
      }, true)
    },
    resizeCharts() { this.charts.forEach(chart => chart.resize()) },
    initParticles() {
      if (window.matchMedia('(prefers-reduced-motion: reduce)').matches || !window.particlesJS) return
      // Particles.js 2.0 的递归合并使用 arguments.callee，在 ES Module 严格模式下会报错；保持库本体不变，替换其公开合并函数。
      Object.deepExtend = function deepExtend(destination, source) {
        Object.keys(source).forEach((property) => {
          if (source[property] && source[property].constructor === Object) {
            destination[property] = destination[property] || {}
            deepExtend(destination[property], source[property])
          } else destination[property] = source[property]
        })
        return destination
      }
      window.particlesJS('particles-js', {
        particles: {
          number: { value: 72, density: { enable: true, value_area: 1100 } },
          color: { value: ['#2ec7c9', '#5ab1ef'] }, shape: { type: 'circle' },
          opacity: { value: .32, random: true }, size: { value: 2, random: true },
          line_linked: { enable: true, distance: 140, color: '#1e6b7d', opacity: .2, width: 1 },
          move: { enable: true, speed: .7, direction: 'none', random: true, straight: false, out_mode: 'out' },
        },
        interactivity: { detect_on: 'canvas', events: { onhover: { enable: true, mode: 'grab' }, onclick: { enable: true, mode: 'push' }, resize: true }, modes: { grab: { distance: 150, line_linked: { opacity: .38 } }, push: { particles_nb: 2 } } },
        retina_detect: true,
      })
    },
    async toggleFullscreen() {
      try {
        if (!document.fullscreenElement) await document.documentElement.requestFullscreen()
        else await document.exitFullscreen()
      } catch (_) { this.error = '当前浏览器不支持全屏模式，可使用浏览器全屏快捷键。' }
    },
    fullscreenChanged() { this.isFullscreen = Boolean(document.fullscreenElement); this.$nextTick(this.resizeCharts) },
  },
  created() { this.updateClock(); this.loadData() },
  mounted() {
    this.initParticles()
    this.clockTimer = window.setInterval(this.updateClock, 1000)
    this.refreshTimer = window.setInterval(this.loadData, 60000)
    window.addEventListener('resize', this.resizeCharts)
    document.addEventListener('fullscreenchange', this.fullscreenChanged)
  },
  beforeDestroy() {
    window.clearInterval(this.clockTimer)
    window.clearInterval(this.refreshTimer)
    window.removeEventListener('resize', this.resizeCharts)
    document.removeEventListener('fullscreenchange', this.fullscreenChanged)
    this.charts.forEach(chart => chart.dispose())
    window.pJSDom?.forEach(item => item.pJS.fn.vendors.destroypJS())
    window.pJSDom = []
  },
}
</script>

<style lang="scss" scoped>
.board-screen {
  --board-bg: #02060b;
  --panel: rgba(7,17,31,.88);
  --line: rgba(58,109,137,.36);
  --cyan: #2ec7c9;
  position: relative;
  width: 100%;
  height: 100dvh;
  min-height: 760px;
  overflow: hidden;
  color: #d5e6f2;
  background: var(--board-bg);
  font-family: "PingFang SC", "Microsoft YaHei", "Noto Sans CJK SC", sans-serif;
}
#particles-js { position: absolute; inset: 0; z-index: 0; }
.board-grid { position: absolute; inset: 0; z-index: 0; pointer-events: none; background-image: linear-gradient(rgba(38,94,119,.045) 1px,transparent 1px),linear-gradient(90deg,rgba(38,94,119,.045) 1px,transparent 1px),radial-gradient(circle at 50% 40%,rgba(16,93,112,.17),transparent 48%); background-size: 48px 48px,48px 48px,100% 100%; }
.board-header { height: 80px; position: relative; z-index: 5; display: grid; grid-template-columns: 1fr auto 1fr; align-items: center; padding: 0 24px; border-bottom: 1px solid var(--line); background: linear-gradient(180deg,rgba(5,15,26,.96),rgba(5,15,26,.66)); }
.board-header::after { content: ""; position: absolute; bottom: -1px; left: 35%; right: 35%; height: 2px; background: var(--cyan); box-shadow: 0 0 18px rgba(46,199,201,.65); }
.header-side { display: flex; align-items: center; gap: 16px; }
.header-right { justify-content: flex-end; }
.board-back { color: #8ba6ba; font-size: 12px; min-height: 40px; display: flex; align-items: center; transition: color .18s; }
.board-back:hover { color: var(--cyan); }
.live-badge { display: flex; align-items: center; gap: 7px; color: #6f95a9; font: 9px var(--mono); letter-spacing: .1em; }
.live-badge i { width: 5px; height: 5px; border-radius: 50%; background: #34d399; box-shadow: 0 0 8px #34d399; animation: live-pulse 1.6s ease-in-out infinite; }
@keyframes live-pulse { 50% { opacity: .35; } }
.board-title { display: flex; align-items: center; gap: 20px; text-align: center; }
.board-title h1 { margin: 0; font-size: clamp(21px,1.75vw,32px); line-height: 1.3; letter-spacing: .16em; color: #e2f6ff; font-weight: 600; text-shadow: 0 0 22px rgba(90,177,239,.3); }
.board-title p { margin: 5px 0 0; color: #4f839c; font: 8px var(--mono); letter-spacing: .32em; }
.title-wing { width: 56px; height: 12px; border-top: 1px solid #26718a; border-left: 2px solid var(--cyan); transform: skewX(-32deg); }
.title-wing.right { transform: scaleX(-1) skewX(-32deg); }
.board-clock { text-align: right; line-height: 1.2; }
.board-clock strong { display: block; color: #c9f5f6; font: 18px var(--mono); letter-spacing: .04em; }
.board-clock span { display: block; color: #66869b; font-size: 9px; margin-top: 5px; }
.icon-button { width: 34px; height: 34px; border: 1px solid var(--line); color: #7ba4b9; background: rgba(11,30,45,.65); font: 18px var(--mono); border-radius: 2px; transition: color .18s,border-color .18s; }
.icon-button:hover { color: var(--cyan); border-color: var(--cyan); }
.icon-button:disabled { opacity: .5; cursor: wait; }
.rotating { display: inline-block; animation: board-spin .8s linear infinite; }
@keyframes board-spin { to { transform: rotate(360deg); } }
.board-error { position: relative; z-index: 6; padding: 5px 20px; text-align: center; color: #ffc1c5; background: rgba(137,38,49,.85); font-size: 11px; }
.board-error button { color: #fff; background: transparent; border: 0; text-decoration: underline; }
.board-layout { position: relative; z-index: 2; height: calc(100dvh - 108px); min-height: 652px; padding: 12px 16px 10px; display: grid; grid-template-columns: minmax(260px,.86fr) minmax(560px,1.8fr) minmax(290px,1fr); gap: 12px; }
.board-column { display: grid; gap: 12px; min-width: 0; min-height: 0; }
.left-column { grid-template-rows: 1.04fr .93fr .88fr; }
.center-column { grid-template-rows: 92px 1.18fr 1fr; }
.right-column { grid-template-rows: .9fr 1.1fr; }
.tech-panel { position: relative; min-width: 0; min-height: 0; overflow: hidden; background: linear-gradient(145deg,rgba(11,27,43,.9),rgba(4,13,23,.87)); border: 1px solid var(--line); box-shadow: inset 0 0 28px rgba(21,81,104,.06); }
.tech-panel::before,.tech-panel::after { content: ""; position: absolute; z-index: 3; width: 12px; height: 12px; pointer-events: none; }
.tech-panel::before { left: -1px; top: -1px; border-left: 2px solid var(--cyan); border-top: 2px solid var(--cyan); }
.tech-panel::after { right: -1px; bottom: -1px; border-right: 2px solid #26718a; border-bottom: 2px solid #26718a; }
.chart { width: 100%; }
.chart-category { height: calc(100% - 44px); }
.chart-source { height: calc(100% - 44px); }
.chart-sentiment { height: calc(100% - 44px); }
.chart-trend { height: calc(100% - 44px); }
.chart-industry { height: calc(100% - 44px); }
.chart-keyword { height: calc(100% - 44px); }
.kpi-grid { display: grid; grid-template-columns: repeat(4,1fr); border: 1px solid var(--line); background: rgba(5,17,29,.82); }
.kpi-item { position: relative; padding: 12px 16px; border-right: 1px solid var(--line); min-width: 0; }
.kpi-item:last-child { border-right: 0; }
.kpi-item > span { display: block; color: #6e91a7; font-size: 9px; white-space: nowrap; }
.kpi-item strong { display: block; margin-top: 4px; color: #e0f7ff; font: 600 clamp(20px,1.6vw,29px)/1.15 var(--mono); letter-spacing: -.05em; font-variant-numeric: tabular-nums; }
.kpi-item.accent strong { color: #54e3d0; text-shadow: 0 0 16px rgba(52,211,153,.22); }
.kpi-item em { color: #6c91a5; font: 10px var(--cjk); margin-left: 4px; }
.kpi-item small { display: block; color: #45677e; font-size: 8px; margin-top: 5px; }
.signal-summary { height: 42px; display: flex; align-items: center; justify-content: space-between; padding: 0 14px; border-bottom: 1px solid var(--line); color: #7f9db1; font-size: 10px; }
.signal-summary > span { display: flex; align-items: center; gap: 6px; }
.signal-summary i { width: 5px; height: 5px; border-radius: 50%; background: #f87171; box-shadow: 0 0 8px #f87171; }
.signal-summary strong { color: #f87171; font: 15px var(--mono); }
.signal-summary small { color: #6e8da1; font-size: 9px; }
.latest-list { padding: 0 12px; }
.latest-item { width: 100%; min-height: 56px; display: grid; grid-template-columns: 24px minmax(0,1fr) auto; align-items: center; gap: 8px; padding: 9px 0; text-align: left; color: inherit; border: 0; border-bottom: 1px solid rgba(58,109,137,.2); background: transparent; transition: background .18s; }
.latest-item:hover { background: rgba(46,199,201,.045); }
.news-index { color: #39687f; font: 10px var(--mono); align-self: start; padding-top: 3px; }
.latest-content { min-width: 0; }
.latest-content strong { display: -webkit-box; overflow: hidden; -webkit-box-orient: vertical; -webkit-line-clamp: 2; color: #b8cbd9; font-size: 11px; line-height: 1.55; font-weight: 400; }
.latest-content small { display: block; margin-top: 4px; color: #4e7188; font-size: 8px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.latest-score { color: #e87980; font: 9px var(--mono); }
.board-footer { position: absolute; z-index: 3; left: 18px; right: 18px; bottom: 2px; height: 22px; display: flex; justify-content: space-between; align-items: center; color: #355b70; font: 8px var(--mono); letter-spacing: .05em; pointer-events: none; }
.board-screen :deep(.modal-backdrop) { font-family: var(--cjk); }

@media (min-width: 1700px) {
  .board-header { height: 88px; }
  .board-layout { height: calc(100dvh - 116px); padding: 16px 20px 12px; gap: 16px; }
  .board-column { gap: 16px; }
  .latest-item { min-height: 62px; }
}
@media (max-width: 1199px) {
  .board-screen { height: auto; min-height: 100dvh; overflow: visible; }
  .board-header { grid-template-columns: 1fr auto; height: auto; min-height: 84px; padding: 12px 18px; }
  .board-title { grid-column: 1 / -1; grid-row: 1; margin-bottom: 12px; }
  .header-side { grid-row: 2; }
  .live-badge { display: none; }
  .title-wing { width: 30px; }
  .board-layout { height: auto; min-height: 0; grid-template-columns: 1fr 1fr; }
  .center-column { grid-column: 1 / -1; grid-row: 1; grid-template-rows: 100px 400px 350px; }
  .left-column,.right-column { grid-template-rows: repeat(3,320px); }
  .right-column { grid-template-rows: 360px 430px; }
  .board-footer { position: relative; left: auto; right: auto; bottom: auto; padding: 8px 18px; height: auto; }
}
@media (max-width: 720px) {
  .board-header { display: flex; flex-wrap: wrap; justify-content: space-between; gap: 10px; }
  .board-title { order: -1; width: 100%; }
  .board-title h1 { font-size: 20px; letter-spacing: .08em; }
  .board-title p { font-size: 7px; letter-spacing: .12em; }
  .title-wing { display: none; }
  .header-left,.header-right { gap: 8px; }
  .board-clock strong { font-size: 14px; }
  .board-clock span { display: none; }
  .board-layout { grid-template-columns: 1fr; padding: 10px; }
  .center-column { grid-column: auto; grid-template-rows: auto 340px 340px; }
  .left-column { grid-template-rows: repeat(3,320px); }
  .right-column { grid-template-rows: 350px 520px; }
  .kpi-grid { grid-template-columns: 1fr 1fr; }
  .kpi-item { min-height: 86px; }
  .kpi-item:nth-child(2) { border-right: 0; }
  .kpi-item:nth-child(-n+2) { border-bottom: 1px solid var(--line); }
  .board-footer { flex-direction: column; gap: 5px; text-align: center; }
}
@media (prefers-reduced-motion: reduce) {
  .live-badge i,.rotating { animation: none; }
}
</style>
