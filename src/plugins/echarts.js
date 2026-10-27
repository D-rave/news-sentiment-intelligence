import * as echarts from 'echarts'

// Apache ECharts 官方 macarons 主题配色与字体设置，显式注册以便按需部署。
const macarons = {
  color: ['#2ec7c9', '#b6a2de', '#5ab1ef', '#ffb980', '#d87a80', '#8d98b3', '#e5cf0d', '#97b552', '#95706d', '#dc69aa', '#07a2a4'],
  backgroundColor: 'rgba(0,0,0,0)',
  textStyle: { fontFamily: 'PingFang SC, Microsoft YaHei, sans-serif', color: '#b9c8d8' },
  title: { textStyle: { color: '#dceeff' }, subtextStyle: { color: '#7f95aa' } },
  line: { itemStyle: { borderWidth: 1 }, lineStyle: { width: 2 }, symbolSize: 5, smooth: false },
  radar: { itemStyle: { borderWidth: 1 }, lineStyle: { width: 2 }, symbolSize: 5 },
  bar: { itemStyle: { barBorderWidth: 0 } },
  pie: { itemStyle: { borderWidth: 0 } },
  categoryAxis: {
    axisLine: { lineStyle: { color: '#35506a' } },
    axisTick: { lineStyle: { color: '#35506a' } },
    axisLabel: { color: '#91a9bd' },
    splitLine: { show: false },
  },
  valueAxis: {
    axisLine: { show: false },
    axisTick: { show: false },
    axisLabel: { color: '#91a9bd' },
    splitLine: { lineStyle: { color: ['#1b3045'], type: 'dashed' } },
  },
  legend: { textStyle: { color: '#9eb4c7' } },
  tooltip: {
    backgroundColor: 'rgba(7,17,31,.94)',
    borderColor: '#284a63',
    textStyle: { color: '#e5f4ff' },
    axisPointer: { lineStyle: { color: '#2ec7c9' }, crossStyle: { color: '#2ec7c9' } },
  },
}

echarts.registerTheme('macarons', macarons)

export const sentimentColors = { 积极: '#34d399', 中性: '#5ab1ef', 消极: '#f87171' }
export default echarts
