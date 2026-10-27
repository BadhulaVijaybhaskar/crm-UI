import { describe, expect, it } from 'vitest'
import {
  buildParentTitleMap,
  buildReadableParentSets,
  filterThreadsByReadableParents,
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

describe('permission-filtered threads', () => {
  const leads = [{ name: 'L1', lead_name: 'Ada', organization: 'Acme' }]
  const deals = [{ name: 'D1', organization: 'Beta Co' }]
  const contacts = [{ name: 'C1', full_name: 'Chris P' }]

  it('keeps only threads whose parent the user can read', () => {
    const sets = buildReadableParentSets({ leads, deals, contacts })
    const threads = [
      {
        id: '1',
        reference_doctype: 'CRM Lead',
        reference_docname: 'L1',
      },
      {
        id: '2',
        reference_doctype: 'CRM Lead',
        reference_docname: 'SECRET',
      },
      {
        id: '3',
        reference_doctype: 'CRM Deal',
        reference_docname: 'D1',
      },
      { id: '4', reference_doctype: null, reference_docname: null },
      {
        id: '5',
        reference_doctype: 'Other',
        reference_docname: 'X',
      },
    ]
    const kept = filterThreadsByReadableParents(threads, sets).map((t) => t.id)
    expect(kept).toEqual(['1', '3', '4'])
  })

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
