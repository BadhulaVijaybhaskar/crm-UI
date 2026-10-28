<template>
  <Dialog v-model:open="show" :size="'sm'" bare>
    <template #default>
      <div class="p-4 pt-5">
        <div class="flex justify-center">
          <div class="flex flex-col items-center">
            <img
              :src="ASTRA_LOGO"
              alt="Astra CRM"
              class="mb-3 h-12 w-auto object-contain"
            />
            <Dialog.Title as-child>
              <h3 class="text-2xl-semibold text-ink-gray-9">Astra CRM</h3>
            </Dialog.Title>
          </div>
        </div>
        <hr class="border-t my-3 mx-2" />
        <p class="text-sm text-ink-gray-6 px-2 mt-2 text-center">
          {{ __('Sales workspace for Astra Connect teams') }}
        </p>
        <div class="mt-4 flex justify-center px-2 pb-1">
          <button
            type="button"
            class="text-xs text-ink-gray-5 underline-offset-2 hover:text-ink-gray-7 hover:underline"
            @click="openLegal"
          >
            {{ __('Legal notices') }}
          </button>
        </div>
      </div>
    </template>
  </Dialog>
</template>
<script setup>
import { ASTRA_LOGO } from '@/assets/brand'
import { Dialog } from 'frappe-ui'
import { useRouter } from 'vue-router'

let show = defineModel({ type: Boolean })
const router = useRouter()

function openLegal() {
  show.value = false
  router.push({ name: 'Legal Notices' })
}
</script>
