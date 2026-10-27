<template>
  <span class="sentiment-tag" :class="className"><i></i>{{ sentiment }}</span>
</template>
<script>
export default {
  props: { sentiment: { type: String, default: '中性' } },
  computed: {
    className() { return { 积极: 'positive', 消极: 'negative', 中性: 'neutral' }[this.sentiment] || 'neutral' },
  },
}
</script>
