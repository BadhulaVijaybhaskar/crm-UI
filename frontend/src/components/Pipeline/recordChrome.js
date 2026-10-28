export function recordTabsClass({ scroll = false } = {}) {
  return [
    'flex min-h-0 flex-1 flex-col bg-crm-bg',
    scroll ? 'overflow-auto' : 'overflow-hidden',
    "[&_[role='tab']]:shrink-0",
    '[&_[data-slot=tab-list]]:min-h-10',
    '[&_[data-slot=tab-list]]:items-end',
    '[&_[data-slot=tab-list]]:gap-0.5',
    '[&_[data-slot=tab-list]]:overflow-x-auto',
    '[&_[data-slot=tab-list]]:border-b',
    '[&_[data-slot=tab-list]]:border-crm-border',
    '[&_[data-slot=tab-list]]:bg-crm-card',
    '[&_[data-slot=tab-list]]:px-crm-page-x',
    '[&_[data-slot=tab-list]::-webkit-scrollbar]:h-0',
    '[&_[data-slot=tab-indicator]]:h-0.5',
    '[&_[data-slot=tab-indicator]>div]:bg-crm-primary',
    '[&_[data-state=inactive]]:text-crm-muted-fg',
    '[&_[data-state=active]]:font-semibold',
    '[&_[data-state=active]]:text-crm-fg',
    '[&_[data-slot=tab-trigger]_svg]:hidden',
    "[&>[role='tabpanel']:not([hidden])]:flex",
    "[&>[role='tabpanel']:not([hidden])]:min-h-0",
    "[&>[role='tabpanel']:not([hidden])]:grow",
    '[&>[data-slot=tab-panel]]:flex',
    '[&>[data-slot=tab-panel]]:min-h-0',
    '[&>[data-slot=tab-panel]]:flex-col',
    '[&>[data-slot=tab-panel]]:overflow-auto',
  ].join(' ')
}

export function metaParts(values) {
  return values
    .map((value) => (value == null ? '' : String(value).trim()))
    .filter(Boolean)
}
