<template>
  <div class="chart-slide">
    <p>{{ reference }}</p>
    <!-- <p>{{ min }}</p> -->
    <div class="slide">
      <SLSlideBar is-int :max="max" :min="min" v-model="_modelValue" :bar-color="barColor" />
    </div>
    <!-- <p>{{ max }}</p> -->
    <!-- 输入框 -->
    <div class="w-16 h-6 border rounded flex items-center p-1">
      <input
        class="w-full h-full border-none outline-none bg-transparent text-xs"
        type="number"
        v-model="_modelValue"
        @change="handleChange"
      />
      <div class="w-3 flex-shrink-0 flex-col flex">
        <SLIcon icon="down" class="w-full h-3 -rotate-180 -mb-1" @click="handleClickUp" />
        <SLIcon icon="down" class="w-full aspect-square" @click="handleClickDown" />
      </div>
    </div>
  </div>
</template>

<script setup>
/**
 * @description: 封装全局slidebar组件，添加一些其他功能
 * @file: SlideBar.vue
 * @since: 2024-01-30 16:18:31
 **/
import { computed } from 'vue'

const props = defineProps({
  max: {
    type: Number,
    required: true
  },
  min: {
    type: Number,
    required: true
  },
  modelValue: {
    type: Number,
    required: true
  },
  barColor: {
    type: String,
    required: true
  },
  reference: {
    type: String,
    default: 'Step'
  }
})

const emits = defineEmits(['update:modelValue', 'change'])

const _modelValue = computed({
  get() {
    return props.modelValue
  },
  set(value) {
    if (value < props.min) {
      return (_modelValue.value = props.min)
    } else if (value > props.max) {
      return (_modelValue.value = props.max)
    }
    emits('update:modelValue', value)
    emits('change', value)
  }
})

// ---------------------------------- 上下键增加/减少数字 ----------------------------------
const handleClickDown = () => {
  if (_modelValue.value > props.min) {
    _modelValue.value = _modelValue.value - 1
  }
}

const handleClickUp = () => {
  if (_modelValue.value < props.max) {
    _modelValue.value = _modelValue.value + 1
  }
}

// ---------------------------------- 当input输入结束时，再次赋值 ----------------------------------
const handleChange = (e) => {
  e.target.value = _modelValue.value
}
</script>

<style lang="scss" scoped>
.chart-slide {
  @apply flex items-center justify-center flex-wrap w-full gap-2 text-dimmer select-none;
  .slide {
    @apply max-w-[230px] w-full;
  }
  input[type='number']::-webkit-inner-spin-button,
  input[type='number']::-webkit-outer-spin-button {
    -webkit-appearance: none;
    margin: 0;
  }
  input[type='number'] {
    -moz-appearance: textfield;
    appearance: textfield;
  }
}
</style>
