<template>
  <main class="page-shell">
    <section class="page-heading">
      <div>
        <h1>财经新闻库</h1>
        <p>从行业、时间与情感倾向三个维度检索 2024 年 A 股相关报道，点击新闻可阅读全文与同行业关联内容。</p>
      </div>
      <div class="page-code">ARCHIVE INDEX<strong>{{ overview.date_range[0] || '—' }}</strong></div>
    </section>

    <section class="metric-strip" aria-label="新闻库概览">
      <div class="metric-item"><div class="metric-label">新闻总量 <span>TOTAL</span></div><div class="metric-value">{{ overview.total.toLocaleString() }}<small>篇</small></div><div class="metric-note">覆盖全年公开报道</div></div>
      <div class="metric-item"><div class="metric-label">行业分类 <span>CLASS</span></div><div class="metric-value">{{ overview.categories }}<small>类</small></div><div class="metric-note">11 个财经行业标签</div></div>
      <div class="metric-item"><div class="metric-label">信息来源 <span>SOURCE</span></div><div class="metric-value">{{ overview.sources }}<small>个</small></div><div class="metric-note">澎湃新闻栏目来源</div></div>
      <div class="metric-item"><div class="metric-label">积极报道占比 <span>POSITIVE</span></div><div class="metric-value">{{ overview.positive_rate }}<small>%</small></div><div class="metric-note">规则辅助情感标签</div></div>
    </section>

    <section class="filter-panel" aria-label="新闻筛选">
      <form class="filter-primary" @submit.prevent="applySearch">
        <label class="search-field">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true"><circle cx="11" cy="11" r="7"></circle><path d="m20 20-4-4"></path></svg>
          <input class="input" v-model.trim="draftKeyword" placeholder="搜索标题、正文或关键词，例如：半导体" aria-label="搜索新闻" />
        </label>
        <select class="select" v-model="filters.sentiment" aria-label="筛选情感" @change="applySearch">
          <option value="全部">全部情感</option><option v-for="item in meta.sentiments" :key="item" :value="item">{{ item }}</option>
        </select>
        <select class="select" v-model="filters.source" aria-label="筛选来源" @change="applySearch">
          <option value="">全部来源</option><option v-for="item in meta.sources" :key="item" :value="item">{{ item }}</option>
        </select>
        <button class="btn" type="submit" :disabled="loading">{{ loading ? '检索中…' : '检索新闻' }}</button>
      </form>
      <div class="category-tabs" role="group" aria-label="按行业分类筛选">
        <button v-for="item in categoryOptions" :key="item" type="button" :class="{ active: filters.category === item }" @click="selectCategory(item)">{{ item }}</button>
      </div>
    </section>

    <div class="result-toolbar">
      <div class="result-count">共找到 <strong>{{ total.toLocaleString() }}</strong> 篇报道<span v-if="filters.q">，关键词“{{ filters.q }}”</span></div>
      <button class="text-button" type="button" @click="resetFilters" v-if="hasFilters">清除全部筛选</button>
      <button class="text-button" type="button" @click="toggleSort" v-else>{{ filters.sort === 'date_desc' ? '按时间倒序 ↓' : '按时间正序 ↑' }}</button>
    </div>

    <div v-if="loading && !items.length" class="state-box"><span class="spinner"></span><strong>正在载入新闻库</strong><p>正在从 Flask 数据接口读取分组结果</p></div>
    <div v-else-if="error" class="state-box"><strong>暂时无法读取新闻</strong><p>{{ error }}</p><button class="btn secondary" @click="loadNews">重新连接</button></div>
    <div v-else-if="!items.length" class="state-box"><strong>没有匹配的报道</strong><p>试试减少筛选条件或更换关键词。</p><button class="btn secondary" @click="resetFilters">查看全部新闻</button></div>
    <section v-else class="news-list" aria-label="新闻检索结果" :aria-busy="loading">
      <article v-for="news in items" :key="news.id" class="news-row" tabindex="0" @click="selectedId = news.id" @keydown.enter="selectedId = news.id">
        <div class="news-date"><strong>{{ dayOf(news.published_at) }}</strong>{{ yearMonth(news.published_at) }}</div>
        <div class="news-main">
          <h2 class="news-title">{{ news.title }}</h2>
          <p class="news-summary">{{ news.summary }}</p>
          <div class="news-meta"><span class="category-label">{{ news.category }}</span><span>{{ news.source }}</span><span v-if="news.keywords[0]"># {{ news.keywords.slice(0, 2).join(' · ') }}</span></div>
        </div>
        <div class="news-sentiment"><SentimentTag :sentiment="news.sentiment" /><span class="score-number">{{ signed(news.sentiment_score) }}</span></div>
      </article>
    </section>

    <nav v-if="pages > 1" class="pagination" aria-label="新闻分页">
      <button type="button" :disabled="filters.page === 1" @click="goPage(filters.page - 1)" aria-label="上一页">‹</button>
      <template v-for="(page, index) in visiblePages">
        <span v-if="page === '…'" :key="`ellipsis-${index}`" class="page-ellipsis">…</span>
        <button v-else type="button" :key="page" :class="{ active: page === filters.page }" :aria-current="page === filters.page ? 'page' : null" @click="goPage(page)">{{ page }}</button>
      </template>
      <button type="button" :disabled="filters.page === pages" @click="goPage(filters.page + 1)" aria-label="下一页">›</button>
    </nav>

    <NewsDetail v-if="selectedId" :key="selectedId" :news-id="selectedId" @close="selectedId = null" @change="selectedId = $event" />
  </main>
</template>

<script>
import NewsDetail from '../components/NewsDetail.vue'
import SentimentTag from '../components/SentimentTag.vue'
import { newsApi } from '../api'

export default {
  components: { NewsDetail, SentimentTag },
  data() {
    return {
      meta: { categories: [], sentiments: [], sources: [], date_range: [] },
      overview: { total: 0, categories: 0, sources: 0, positive_rate: 0, date_range: [] },
      filters: { q: '', category: '全部', sentiment: '全部', source: '', sort: 'date_desc', page: 1 },
      draftKeyword: '', items: [], total: 0, pages: 0, loading: false, error: '', selectedId: null, requestId: 0,
    }
  },
  computed: {
    categoryOptions() { return ['全部', ...this.meta.categories] },
    hasFilters() { return this.filters.q || this.filters.category !== '全部' || this.filters.sentiment !== '全部' || this.filters.source },
    visiblePages() {
      if (this.pages <= 7) return Array.from({ length: this.pages }, (_, i) => i + 1)
      const current = this.filters.page
      const pages = [1]
      if (current > 4) pages.push('…')
      for (let i = Math.max(2, current - 1); i <= Math.min(this.pages - 1, current + 1); i++) pages.push(i)
      if (current < this.pages - 3) pages.push('…')
      pages.push(this.pages)
      return pages
    },
  },
  methods: {
    dayOf(value) { return value.slice(8, 10) },
    yearMonth(value) { return value.slice(0, 7).replace('-', ' / ') },
    signed(value) { return `${value > 0 ? '+' : ''}${Number(value).toFixed(3)}` },
    async loadBase() {
      try {
        const [meta, overview] = await Promise.all([newsApi.meta(), newsApi.overview()])
        this.meta = meta
        this.overview = overview
      } catch (error) { this.error = error.message }
    },
    async loadNews() {
      const id = ++this.requestId
      this.loading = true
      this.error = ''
      try {
        const data = await newsApi.list({ ...this.filters, page_size: 12 })
        if (id !== this.requestId) return
        this.items = data.items
        this.total = data.total
        this.pages = data.pages
      } catch (error) { if (id === this.requestId) this.error = error.message } finally { if (id === this.requestId) this.loading = false }
    },
    applySearch() { this.filters.q = this.draftKeyword; this.filters.page = 1; this.loadNews() },
    selectCategory(category) { this.filters.category = category; this.filters.page = 1; this.loadNews() },
    toggleSort() { this.filters.sort = this.filters.sort === 'date_desc' ? 'date_asc' : 'date_desc'; this.filters.page = 1; this.loadNews() },
    goPage(page) { if (page < 1 || page > this.pages || page === this.filters.page) return; this.filters.page = page; this.loadNews(); window.scrollTo({ top: 500, behavior: 'smooth' }) },
    resetFilters() {
      this.filters = { q: '', category: '全部', sentiment: '全部', source: '', sort: 'date_desc', page: 1 }
      this.draftKeyword = ''
      this.loadNews()
    },
  },
  created() { this.loadBase(); this.loadNews() },
}
</script>
