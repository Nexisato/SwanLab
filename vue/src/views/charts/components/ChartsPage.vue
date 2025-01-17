<template>
  <ChartsContainer v-for="group in groups" :key="group.name" :label="group.name" :charts="group.charts" />
</template>

<script setup>
/**
 * @description: 项目对比图表，本组件完成项目对比图表的数据的请求和展示
 * 这个组件是为了实现自动刷新的无奈之举（在websocket没有上之前），整个组件刷新的时候，会重新请求数据
 * @file: ChartsPage.vue
 * @since: 2024-02-06 17:17:55
 **/
import ChartsContainer from '@swanlab-vue/charts/ChartsContainer.vue'
import { useProjectStore } from '@swanlab-vue/store'
import { provide, onUnmounted } from 'vue'
import http from '@swanlab-vue/api/http'
const props = defineProps({
  // 图表组
  groups: {
    type: Array,
    required: true
  },
  // 图表列表
  charts: {
    type: Array,
    required: true
  }
})
const projectStore = useProjectStore()

// ---------------------------------- 轮询器 ----------------------------------
const intervalMap = new Map()
const createInterval = (exp_name, cid, callback) => {
  const interval = setInterval(() => {
    getTagDataByExpName(exp_name, cid, callback)
  }, 5000)
  intervalMap.set(exp_name + '-' + cid, interval)
}

onUnmounted(() => {
  intervalMap.forEach((interval) => {
    clearInterval(interval)
  })
})

// ---------------------------------- 数据驱动 ----------------------------------

provide('$on', (sources, cid, callback) => {
  // 获取数据
  sources.map((exp_name) => {
    // 如果exp_name对应的实验的show为0，则跳过
    if (projectStore.experiments.find((exp) => exp.name === exp_name).show === 0) return callback(exp_name, null, null)
    getTagDataByExpName(exp_name, cid, callback)
    // 判断当前实验状态
    if (projectStore.experiments.find((exp) => exp.name === exp_name).status === 0) {
      // 开启轮询
      createInterval(exp_name, cid, callback)
    }
  })
})

// 暂时注销订阅不写任何逻辑
provide('$off', () => {})

// ---------------------------------- 请求数据 ----------------------------------

/**
 * @description: 根据实验名称获取标签数据
 * @param {string} exp_name 实验名称
 * @param {number} cid 图表id
 */
const getTagDataByExpName = (exp_name, cid, callback) => {
  const exp_id = projectStore.experiments.find((exp) => exp.name === exp_name).id
  const tag_name = props.charts.find((chart) => chart.id === cid).name
  http
    .get(`/experiment/${exp_id}/tag/${tag_name}`)
    .then((res) => {
      callback(exp_name, res.data, null)
    })
    .catch(() => {
      callback(exp_name, null, null)
    })
}
</script>

<style lang="scss" scoped></style>
