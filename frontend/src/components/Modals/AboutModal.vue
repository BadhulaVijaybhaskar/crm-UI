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
      </div>
    </template>
  </Dialog>
</template>
<script setup>
import { ASTRA_LOGO } from '@/assets/brand'
import { Dialog } from 'frappe-ui'

let show = defineModel({ type: Boolean })
</script>
