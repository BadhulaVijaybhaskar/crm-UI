import { describe, expect, it } from 'vitest'
import {
  CONVERSATIONS_MAX_PAGES,
  CONVERSATIONS_TARGET_VISIBLE,
  buildParentTitleMap,
  conversationSourcesToAdvance,
  shouldFetchNextConversationPage,
  threadDisplayTitle,
  waMessageReference,
} from '@/components/astra/conversations/conversationHelpers'

describe('waMessageReference', () => {
  it('reads reference_docname (not reference_name)', () => {
    expect(
      waMessageReference({
        reference_docname: 'CRM-LEAD-001',
        reference_name: 'wrong',
      }),
    ).toBe('CRM-LEAD-001')
    expect(waMessageReference({ reference_name: 'only-wrong' })).toBe(null)
    expect(waMessageReference(null)).toBe(null)
  })
})

describe('thread display titles', () => {
  const leads = [{ name: 'L1', lead_name: 'Ada', organization: 'Acme' }]
  const deals = [{ name: 'D1', organization: 'Beta Co' }]
  const contacts = [{ name: 'C1', full_name: 'Chris P' }]

  it('shows lead/deal display names instead of record ids', () => {
    const titles = buildParentTitleMap({ leads, deals, contacts })
    expect(
      threadDisplayTitle(
        {
          reference_doctype: 'CRM Lead',
          reference_docname: 'L1',
          fallback: 'L1',
        },
        titles,
      ),
    ).toBe('Ada · Acme')
    expect(
      threadDisplayTitle(
        {
          reference_doctype: 'CRM Deal',
          reference_docname: 'D1',
          fallback: 'D1',
        },
        titles,
      ),
    ).toBe('Beta Co')
    expect(
      threadDisplayTitle(
        {
          reference_doctype: 'CRM Lead',
          reference_docname: 'UNKNOWN',
          fallback: 'fallback',
        },
        titles,
      ),
    ).toBe('fallback')
  })
})

describe('conversation list pagination fill', () => {
  it('fetches another page until the visible target is reached', () => {
    expect(
      shouldFetchNextConversationPage({
        visibleCount: 10,
        targetCount: CONVERSATIONS_TARGET_VISIBLE,
        hasNextPage: true,
        pagesFetched: 1,
        maxPages: CONVERSATIONS_MAX_PAGES,
      }),
    ).toBe(true)
  })

  it('stops when the visible list is full, pages are exhausted, or cap hit', () => {
    expect(
      shouldFetchNextConversationPage({
        visibleCount: CONVERSATIONS_TARGET_VISIBLE,
        hasNextPage: true,
        pagesFetched: 1,
      }),
    ).toBe(false)
    expect(
      shouldFetchNextConversationPage({
        visibleCount: 5,
        hasNextPage: false,
        pagesFetched: 1,
      }),
    ).toBe(false)
    expect(
      shouldFetchNextConversationPage({
        visibleCount: 5,
        hasNextPage: true,
        pagesFetched: CONVERSATIONS_MAX_PAGES,
        maxPages: CONVERSATIONS_MAX_PAGES,
      }),
    ).toBe(false)
    expect(
      shouldFetchNextConversationPage({
        visibleCount: 5,
        hasNextPage: true,
        pagesFetched: 1,
        loading: true,
      }),
    ).toBe(false)
  })

  it('advances only sources that still have pages under the cap', () => {
    const keys = conversationSourcesToAdvance(
      [
        { key: 'calls', hasNextPage: true, loading: false, pagesFetched: 1 },
        { key: 'emails', hasNextPage: false, loading: false, pagesFetched: 1 },
        {
          key: 'notes',
          hasNextPage: true,
          loading: false,
          pagesFetched: CONVERSATIONS_MAX_PAGES,
        },
        { key: 'wa', hasNextPage: true, loading: true, pagesFetched: 1 },
      ],
      { visibleCount: 8, targetCount: 40, maxPages: CONVERSATIONS_MAX_PAGES },
    )
    expect(keys).toEqual(['calls'])
  })

  it('does not advance any source once the visible target is met', () => {
    expect(
      conversationSourcesToAdvance(
        [{ key: 'calls', hasNextPage: true, loading: false, pagesFetched: 1 }],
        { visibleCount: 40, targetCount: 40 },
      ),
    ).toEqual([])
  })
})
