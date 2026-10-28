<template>
  <!-- crm.css .nav li — height 32, radius 6, pad 0 10, gap 10, font 13/500.
       Do NOT use <component :is="'button'"> — unplugin resolves that to frappe-ui Button. -->
  <RouterLink
    v-if="to"
    :to="to"
    class="astra-nav-item"
    :class="{ 'astra-nav-item--on': active }"
    :aria-current="active ? 'page' : undefined"
    @click="onClick"
  >
    <span class="astra-nav-item__icon">
      <slot name="prefix" />
    </span>
    <span class="astra-nav-item__label">
      <slot>{{ label }}</slot>
    </span>
    <span v-if="count != null" class="astra-nav-item__count">{{ count }}</span>
    <span v-if="external" class="astra-nav-item__ext" aria-hidden="true">
      <slot name="ext" />
    </span>
  </RouterLink>
  <button
    v-else
    type="button"
    class="astra-nav-item"
    :class="{ 'astra-nav-item--on': active }"
    :aria-current="active ? 'page' : undefined"
    @click="onClick"
  >
    <span class="astra-nav-item__icon">
      <slot name="prefix" />
    </span>
    <span class="astra-nav-item__label">
      <slot>{{ label }}</slot>
    </span>
    <span v-if="count != null" class="astra-nav-item__count">{{ count }}</span>
    <span v-if="external" class="astra-nav-item__ext" aria-hidden="true">
      <slot name="ext" />
    </span>
  </button>
</template>

<script setup>
import { RouterLink } from 'vue-router'

defineProps({
  label: { type: String, default: '' },
  to: { type: [String, Object], default: null },
  active: { type: Boolean, default: false },
  count: { type: [Number, String], default: null },
  external: { type: Boolean, default: false },
})

const emit = defineEmits(['click'])

function onClick(event) {
  emit('click', event)
}
</script>

<style scoped>
.astra-nav-item {
  display: flex;
  align-items: center;
  gap: 10px;
  height: 32px;
  padding: 0 10px;
  border: 0;
  border-radius: 6px;
  background: transparent;
  color: var(--crm-nav-fg);
  /* Avoid `font:` shorthand — it resets font-feature-settings (cv11/ss01). */
  font-family: var(--font-sans);
  font-size: 13px;
  font-weight: 500;
  line-height: 1.45;
  font-feature-settings: 'cv11', 'ss01';
  -webkit-font-smoothing: antialiased;
  text-decoration: none;
  width: 100%;
  text-align: left;
  cursor: pointer;
  box-sizing: border-box;
}
.astra-nav-item:hover {
  background: rgba(15, 42, 54, 0.55);
  color: #fff;
}
.astra-nav-item--on {
  background: var(--crm-nav-active);
  color: #fff;
  box-shadow: inset 3px 0 0 var(--crm-nav-indicator);
}
.astra-nav-item__icon {
  display: grid;
  place-items: center;
  width: 16px;
  height: 16px;
  flex: none;
  color: var(--crm-nav-faint);
}
.astra-nav-item--on .astra-nav-item__icon {
  color: var(--crm-nav-indicator);
}
.astra-nav-item__icon :deep(svg) {
  width: 16px;
  height: 16px;
}
.astra-nav-item__label {
  min-width: 0;
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.astra-nav-item__count {
  margin-left: auto;
  font-size: 11px;
  font-weight: 600;
  color: var(--crm-nav-faint);
  flex: none;
  /* match app.css .nav li .cnt — no tabular-nums */
  font-feature-settings: 'cv11', 'ss01';
  -webkit-font-smoothing: antialiased;
}
.astra-nav-item--on .astra-nav-item__count {
  color: #c4d2da;
}
.astra-nav-item__ext {
  margin-left: auto;
  width: 12px;
  height: 12px;
  color: var(--crm-nav-faint);
  flex: none;
  display: grid;
  place-items: center;
}
.astra-nav-item__ext :deep(svg) {
  width: 12px;
  height: 12px;
}
.astra-nav-item__count + .astra-nav-item__ext {
  margin-left: 0;
}
</style>
