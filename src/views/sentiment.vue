<template>
  <main class="page-shell">
    <section class="page-heading">
      <div><h1>情感洞察</h1><p>观察全年新闻情绪的月度变化、行业差异与风险报道。得分范围为 −1 至 +1，数值越高表示文本中的积极信号越集中。</p></div>
      <div class="page-code">SENTIMENT INDEX<strong>{{ signed(overview.average_score) }}</strong></div>
    </section>

    <section class="metric-strip" aria-label="情感分析概览">
      <div class="metric-item"><div class="metric-label">平均情感得分 <span>MEAN</span></div><div class="metric-value">{{ signed(overview.average_score) }}</div><div class="metric-note">全年报道文本均值</div></div>
      <div class="metric-item"><div class="metric-label">积极报道占比 <span>POSITIVE</span></div><div class="metric-value">{{ overview.positive_rate }}<small>%</small></div><div class="metric-note">正向财经信号</div></div>
      <div class="metric-item"><div class="metric-label">消极报道 <span>NEGATIVE</span></div><div class="metric-value">{{ overview.negative_count }}<small>篇</small></div><div class="metric-note">需关注的风险信息</div></div>
      <div class="metric-item"><div class="metric-label">分析样本 <span>SAMPLES</span></div><div class="metric-value">{{ overview.total.toLocaleString() }}<small>篇</small></div><div class="metric-note">{{ overview.date_range.join(' 至 ') }}</div></div>
    </section>

    <div v-if="error" class="state-box"><strong>分析数据加载失败</strong><p>{{ error }}</p><button class="btn secondary" @click="load">重新加载</button></div>
    <template v-else>
      <section class="analysis-grid">
        <article class="chart-card">
          <div class="chart-card-header"><div><h2>月度情感走势</h2><p>情感数量与平均得分对照</p></div><span class="chart-index">01 / TREND</span></div>
          <div ref="trend" class="chart-body" role="img" aria-label="月度情感数量与平均得分折线图"></div>
        </article>
        <article class="chart-card">
          <div class="chart-card-header"><div><h2>近期风险报道</h2><p>按发布时间选取消极标签新闻</p></div><span class="chart-index">02 / RISK</span></div>
          <div class="risk-list">
            <div v-if="loading" class="state-box"><span class="spinner"></span></div>
            <button v-for="news in negativeNews" v-else :key="news.id" class="risk-item" @click="selectedId = news.id">
              <span class="risk-title">{{ news.title }}</span><span class="risk-score">{{ signed(news.sentiment_score) }}</span>
              <span class="risk-meta">{{ news.published_at }} · {{ news.category }} · {{ news.source }}</span>
            </button>
          </div>
        </article>
      </section>

      <section class="analysis-grid equal">
        <article class="chart-card">
          <div class="chart-card-header"><div><h2>行业情感构成</h2><p>各行业积极、中性与消极报道数量</p></div><span class="chart-index">03 / INDUSTRY</span></div>
          <div ref="industry" class="chart-body tall" role="img" aria-label="行业情感构成堆叠条形图"></div>
        </article>
        <article class="chart-card">
          <div class="chart-card-header"><div><h2>行业情绪温差</h2><p>各行业平均情感得分，右侧偏积极</p></div><span class="chart-index">04 / SCORE</span></div>
          <div ref="score" class="chart-body tall" role="img" aria-label="行业平均情感得分发散条形图"></div>
        </article>
      </section>
      <div class="analysis-note">分析说明：标签与得分由财经情感词典规则生成，适合课程研究与趋势演示，不代表真实股价涨跌或投资建议。</div>
    </template>
    <NewsDetail v-if="selectedId" :key="selectedId" :news-id="selectedId" @close="selectedId = null" @change="selectedId = $event" />
  </main>
</template>

<script>
import NewsDetail from '../components/NewsDetail.vue'
import { newsApi } from '../api'
import echarts, { sentimentColors } from '../plugins/echarts'

export default {
  components: { NewsDetail },
  data() {
    return {
      overview: { total: 0, average_score: 0, positive_rate: 0, negative_count: 0, date_range: [] },
      negativeNews: [], selectedId: null, loading: true, error: '', charts: [],
    }
  },
  methods: {
    signed(value) { const number = Number(value || 0); return `${number > 0 ? '+' : ''}${number.toFixed(3)}` },
    async load() {
      this.loading = true
      this.error = ''
      try {
        const [overview, trend, categories, negative] = await Promise.all([
          newsApi.overview(), newsApi.trend(), newsApi.categorySentiment(), newsApi.list({ sentiment: '消极', page_size: 5, sort: 'date_desc' }),
        ])
        this.overview = overview
        this.negativeNews = negative.items
        this.$nextTick(() => { this.renderTrend(trend); this.renderIndustry(categories); this.renderScore(categories) })
      } catch (error) { this.error = error.message } finally { this.loading = false }
    },
    initChart(ref) {
      const chart = echarts.init(this.$refs[ref], null, { renderer: 'canvas' })
      this.charts.push(chart)
      return chart
    },
    renderTrend(data) {
      const chart = this.initChart('trend')
      chart.setOption({
        color: [sentimentColors.积极, sentimentColors.消极, '#0e8996'],
        tooltip: { trigger: 'axis', axisPointer: { type: 'cross' } },
        legend: { top: 14, right: 16, data: ['积极报道', '消极报道', '平均得分'] },
        grid: { left: 50, right: 56, top: 66, bottom: 42 },
        xAxis: { type: 'category', data: data.months.map(m => `${Number(m.slice(5))}月`), axisTick: { show: false }, axisLine: { lineStyle: { color: '#cbd5dc' } }, axisLabel: { color: '#687386' } },
        yAxis: [
          { type: 'value', name: '报道数', nameTextStyle: { color: '#687386' }, splitLine: { lineStyle: { color: '#edf0f2' } }, axisLabel: { color: '#687386' } },
          { type: 'value', name: '得分', min: -0.3, max: 0.5, splitLine: { show: false }, axisLabel: { color: '#687386' } },
        ],
        series: [
          { name: '积极报道', type: 'bar', stack: 'sentiment', data: data.positive, barMaxWidth: 28 },
          { name: '消极报道', type: 'bar', stack: 'sentiment', data: data.negative, barMaxWidth: 28 },
          { name: '平均得分', type: 'line', yAxisIndex: 1, data: data.score, smooth: .25, symbolSize: 7, lineStyle: { width: 2.5 }, areaStyle: { opacity: .06 } },
        ],
      })
    },
    renderIndustry(data) {
      const ordered = [...data].reverse()
      const chart = this.initChart('industry')
      chart.setOption({
        color: [sentimentColors.积极, sentimentColors.中性, sentimentColors.消极],
        tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
        legend: { top: 12, right: 12 },
        grid: { left: 68, right: 22, top: 54, bottom: 28 },
        xAxis: { type: 'value', splitLine: { lineStyle: { color: '#edf0f2' } }, axisLabel: { color: '#687386' } },
        yAxis: { type: 'category', data: ordered.map(d => d.category), axisTick: { show: false }, axisLine: { show: false }, axisLabel: { color: '#3e4757' } },
        series: [
          { name: '积极', type: 'bar', stack: 'total', data: ordered.map(d => d.positive), barMaxWidth: 15 },
          { name: '中性', type: 'bar', stack: 'total', data: ordered.map(d => d.neutral), barMaxWidth: 15 },
          { name: '消极', type: 'bar', stack: 'total', data: ordered.map(d => d.negative), barMaxWidth: 15 },
        ],
      })
    },
    renderScore(data) {
      const ordered = [...data].sort((a, b) => a.average_score - b.average_score)
      const chart = this.initChart('score')
      chart.setOption({
        tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' }, formatter: params => `${params[0].name}<br/>平均得分：${this.signed(params[0].value)}` },
        grid: { left: 68, right: 28, top: 34, bottom: 36 },
        xAxis: { type: 'value', min: -0.2, max: 0.4, splitLine: { lineStyle: { color: '#edf0f2' } }, axisLabel: { color: '#687386' } },
        yAxis: { type: 'category', data: ordered.map(d => d.category), axisTick: { show: false }, axisLine: { show: false }, axisLabel: { color: '#3e4757' } },
        series: [{ type: 'bar', data: ordered.map(d => ({ value: d.average_score, itemStyle: { color: d.average_score >= 0 ? '#0e8996' : '#bd4149' } })), barMaxWidth: 16, markLine: { silent: true, symbol: 'none', label: { show: false }, lineStyle: { color: '#9aa6b2', type: 'dashed' }, data: [{ xAxis: 0 }] } }],
      })
    },
    resizeCharts() { this.charts.forEach(chart => chart.resize()) },
  },
  created() { this.load() },
  mounted() { window.addEventListener('resize', this.resizeCharts) },
  beforeDestroy() { window.removeEventListener('resize', this.resizeCharts); this.charts.forEach(chart => chart.dispose()) },
}
</script>
