<template>
  <div id="app" :class="{ 'is-board': isBoard }">
    <header v-if="!isBoard" class="site-header">
      <div class="header-inner">
        <router-link to="/news" class="brand" aria-label="闻见新闻分析首页">
          <span class="brand-mark" aria-hidden="true"><i></i><i></i><i></i></span>
          <span><strong>闻见</strong><small>NEWS INTELLIGENCE</small></span>
        </router-link>
        <nav class="main-nav" aria-label="主导航">
          <router-link to="/news">新闻库</router-link>
          <router-link to="/sentiment">情感洞察</router-link>
          <router-link to="/board" class="board-link">可视化大屏<span>↗</span></router-link>
        </nav>
        <div class="header-meta"><span class="status-dot"></span>2024 年度新闻库</div>
      </div>
    </header>
    <router-view />
    <footer v-if="!isBoard" class="site-footer">
      <span>闻见 · 财经新闻智能分析系统</span>
      <span>数据来源：用户提供的澎湃新闻数据集 · 分析标签为规则辅助结果</span>
    </footer>
  </div>
</template>

<script>
export default {
  name: 'App',
  computed: {
    isBoard() { return this.$route.name === 'board' },
  },
  watch: {
    '$route.meta.title': {
      immediate: true,
      handler(title) { document.title = `${title || '新闻分析'} · 闻见` },
    },
  },
}
</script>
