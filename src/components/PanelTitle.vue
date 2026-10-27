<template>
  <header class="panel-title">
    <span class="panel-index">{{ index }}</span>
    <h2>{{ title }}<small>{{ subtitle }}</small></h2>
    <span class="panel-line"></span>
    <span class="panel-node"></span>
  </header>
</template>
<script>
export default { props: { index: String, title: String, subtitle: String } }
</script>
<style lang="scss" scoped>
.panel-title { height: 44px; padding: 0 12px; display: flex; align-items: center; gap: 8px; border-bottom: 1px solid rgba(58,109,137,.24); background: linear-gradient(90deg,rgba(27,79,98,.12),transparent); }
.panel-index { color: #2ec7c9; font: 9px "SFMono-Regular",Consolas,monospace; }
.panel-title h2 { margin: 0; color: #c8dce9; font-size: 12px; line-height: 1.2; font-weight: 500; letter-spacing: .06em; white-space: nowrap; }
.panel-title small { display: block; margin-top: 4px; color: #3d687f; font: 7px "SFMono-Regular",Consolas,monospace; letter-spacing: .08em; }
.panel-line { height: 1px; flex: 1; background: linear-gradient(90deg,rgba(46,199,201,.3),transparent); }
.panel-node { width: 4px; height: 4px; transform: rotate(45deg); background: #2ec7c9; box-shadow: 0 0 7px #2ec7c9; }
</style>
