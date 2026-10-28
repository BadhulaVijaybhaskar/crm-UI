/**
 * Minimal window boot blob so the production SPA mounts without Frappe/Jinja.
 * TEST ONLY — written into the served HTML by the parity static server.
 */
export function buildBoot({ theme = 'light' } = {}) {
  return {
    default_route: '/crm',
    site_name: 'parity.local',
    read_only_mode: 0,
    csrf_token: 'parity-csrf-token',
    setup_complete: 1,
    sysdefaults: {
      app_name: 'Astra CRM',
      otp_issuer_name: 'Astra CRM',
      date_format: 'dd-mm-yyyy',
      time_format: 'HH:mm:ss',
      float_precision: 2,
      currency: 'INR',
    },
    app_name: 'Astra CRM',
    is_demo_site: 0,
    demo_data_created: 0,
    is_fc_site: 0,
    translated_doctypes: [],
    translated_messages: {},
    timezone: { system: 'Asia/Kolkata', user: 'Asia/Kolkata' },
    state_options: {},
    erp_integration_available: 0,
    astra_connect_enabled: 1,
    astra_connect_url: 'https://connect.parity.test',
    // Hint for theme before Vue hydrates useColorScheme
    parity_theme: theme,
  }
}

export function bootScript(boot) {
  const lines = Object.entries(boot).map(
    ([k, v]) => `window[${JSON.stringify(k)}] = ${JSON.stringify(v)};`,
  )
  return `<script>\n${lines.join('\n')}\n</script>`
}
