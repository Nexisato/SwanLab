<template>
  <div class="flex flex-col min-h-full bg-higher">
    <!-- 第一行内容，项目标题、实验标题、编辑按钮、删除按钮 -->
    <div class="project-title transition-marging duration-300 mt-5 pl-6" :class="{ 'ml-8': !isSideBarShow }">
      <div class="flex items-center gap-3">
        <!-- 项目标题/实验标题 -->
        <h1 class="text-2xl items-center gap-1 font-semibold max-w-md truncate">
          {{ projectStore.name }}
        </h1>
      </div>
    </div>
    <ChartsPage :groups="groups" :charts="charts" :key="chartsPageKey" v-if="groups.length" />
    <!-- 图表不存在 -->
    <p class="font-semibold pt-5 text-center" v-else>Empty Charts</p>
  </div>
</template>

<script setup>
/**
 * @description: 项目对比图表，本组件完成项目对比图表的数据的请求和展示，大致流程是：
 * 1. 通过 http.get('/project/charts') 请求项目对比图表的数据，渲染到页面上
 * 2. 根据每个图表的数据源
 * @file: ChartsView.vue
 * @since: 2024-01-27 13:05:27
 **/
import http from '@swanlab-vue/api/http'
import { useProjectStore } from '@swanlab-vue/store'
import { ref, provide, inject } from 'vue'
import ChartsPage from './components/ChartsPage.vue'
import { onUnmounted } from 'vue'
const projectStore = useProjectStore()
http.get('/project/charts').then(({ data }) => {
  // 将namespaces转换为groups
  charts.value = data.charts
  namespaces.value = data.namespaces
  groups.value = generateGroups()
})
const isSideBarShow = inject('isSideBarShow')

// ---------------------------------- 数据驱动 ----------------------------------
// 项目对比图表数据，[{name, charts: [charts]}]
const groups = ref([])
const charts = ref([])
const namespaces = ref([])
const chartsPageKey = ref(0)

const generateGroups = () => {
  // 生成groups
  const groups = []
  namespaces.value.forEach((namespace) => {
    const group = {
      name: namespace.name,
      charts: []
    }
    namespace.charts.forEach((chart_id) => {
      const chart = charts.value.find((chart) => {
        return chart.id === chart_id
      })
      // 如果chart的所有source都为不可见，不push
      if (chart.source.every((source) => !projectStore.showMap[source])) return
      // 如果在source中不在error的keys中的都不可见，不push
      // 首先找到所有source中不在error的keys中的source
      const sources = chart.source.filter((source) => !chart.error[source])
      if (sources.every((source) => !projectStore.showMap[source])) return

      group.charts.push(chart)
    })
    // 如果group的所有chart都为不可见，不push
    if (group.charts.length) groups.push(group)
  })
  return groups
}

// ---------------------------------- 向projectStore注册回调，当点击眼睛时执行此回调 ----------------------------------
const handleShowChange = () => {
  // 重新渲染页面
  chartsPageKey.value++
  // 重新生成groups
  groups.value = generateGroups()
}

projectStore.registerChangeShowCallback(handleShowChange)

onUnmounted(() => {
  projectStore.destoryChangeShowCallback()
})

// ---------------------------------- 色盘注入 ----------------------------------
const createGetSeriesColor = () => {
  // 遍历所有实验，实验名称为key，实验颜色为value
  const colors = projectStore.colorMap
  return (exp_name) => {
    return colors[exp_name]
  }
}
const colors = [...projectStore.colors]
colors.getSeriesColor = createGetSeriesColor()
// console.log(colors)
provide('colors', colors)
</script>

<style lang="scss" scoped></style>
