<template>
  <div class="modal-backdrop" @click.self="$emit('close')" @keydown.esc="$emit('close')">
    <section class="detail-drawer" role="dialog" aria-modal="true" aria-labelledby="detail-title" tabindex="-1" ref="drawer">
      <button class="drawer-close" type="button" aria-label="关闭新闻详情" @click="$emit('close')" ref="close">×</button>
      <div v-if="loading" class="state-box"><span class="spinner"></span><strong>正在读取新闻</strong></div>
      <div v-else-if="error" class="state-box"><strong>详情加载失败</strong><p>{{ error }}</p><button class="btn secondary" @click="load">重新加载</button></div>
      <template v-else-if="item">
        <div class="detail-kicker">NEWS ARCHIVE / {{ String(item.id).padStart(5, '0') }}</div>
        <h2 class="detail-title" id="detail-title">{{ item.title }}</h2>
        <div class="detail-info">
          <span>{{ item.published_at }}</span><span>{{ item.source }}</span>
          <span class="category-label">{{ item.category }}</span>
          <SentimentTag :sentiment="item.sentiment" />
          <span>情感得分 {{ formatScore(item.sentiment_score) }}</span>
        </div>
        <article class="detail-content">{{ item.content }}</article>
        <div class="detail-keywords" v-if="item.keywords.length">
          <span v-for="word in item.keywords" :key="word" class="keyword-chip">{{ word }}</span>
        </div>
        <div class="analysis-note">当前标签由可复现的财经词典规则生成，仅用于文本倾向研究，不构成任何投资建议。</div>
        <template v-if="related.length">
          <h3 class="related-title">同行业相关新闻</h3>
          <button v-for="news in related" :key="news.id" class="related-item" @click="openRelated(news.id)">
            {{ news.title }}<span>{{ news.published_at }} · {{ news.source }}</span>
          </button>
        </template>
      </template>
    </section>
  </div>
</template>

<script>
import SentimentTag from './SentimentTag.vue'
import { newsApi } from '../api'

export default {
  components: { SentimentTag },
  props: { newsId: { type: Number, required: true } },
  data() { return { item: null, related: [], loading: true, error: '' } },
  methods: {
    formatScore(value) { return `${value > 0 ? '+' : ''}${Number(value).toFixed(3)}` },
    async load() {
      this.loading = true
      this.error = ''
      try {
        const data = await newsApi.detail(this.newsId)
        this.item = data.item
        this.related = data.related
        this.$nextTick(() => this.$refs.close?.focus())
      } catch (error) { this.error = error.message } finally { this.loading = false }
    },
    openRelated(id) {
      this.$emit('change', id)
      this.$refs.drawer.scrollTo({ top: 0, behavior: 'smooth' })
    },
    onKeydown(event) { if (event.key === 'Escape') this.$emit('close') },
  },
  created() { this.load() },
  mounted() {
    document.body.style.overflow = 'hidden'
    document.addEventListener('keydown', this.onKeydown)
  },
  beforeDestroy() {
    document.body.style.overflow = ''
    document.removeEventListener('keydown', this.onKeydown)
  },
}
</script>
