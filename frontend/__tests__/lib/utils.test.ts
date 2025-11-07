describe('Utility Functions', () => {
  describe('formatCurrency', () => {
    it('formats numbers as currency', () => {
      const formatCurrency = (value: number) => {
        return new Intl.NumberFormat('en-US', {
          style: 'currency',
          currency: 'USD',
        }).format(value)
      }

      expect(formatCurrency(1000)).toBe('$1,000.00')
      expect(formatCurrency(1500000)).toBe('$1,500,000.00')
      expect(formatCurrency(0)).toBe('$0.00')
    })

    it('handles negative values', () => {
      const formatCurrency = (value: number) => {
        return new Intl.NumberFormat('en-US', {
          style: 'currency',
          currency: 'USD',
        }).format(value)
      }

      expect(formatCurrency(-1000)).toBe('-$1,000.00')
    })
  })

  describe('formatPercentage', () => {
    it('formats numbers as percentages', () => {
      const formatPercentage = (value: number, decimals = 1) => {
        return `${(value * 100).toFixed(decimals)}%`
      }

      expect(formatPercentage(0.15)).toBe('15.0%')
      expect(formatPercentage(0.125, 2)).toBe('12.50%')
      expect(formatPercentage(1.5)).toBe('150.0%')
    })
  })

  describe('formatMultiple', () => {
    it('formats numbers as multiples (e.g., DPI, TVPI)', () => {
      const formatMultiple = (value: number, decimals = 2) => {
        return `${value.toFixed(decimals)}x`
      }

      expect(formatMultiple(1.5)).toBe('1.50x')
      expect(formatMultiple(2.345, 3)).toBe('2.345x')
      expect(formatMultiple(0)).toBe('0.00x')
    })
  })

  describe('formatCompactCurrency', () => {
    it('formats large numbers with compact notation', () => {
      const formatCompactCurrency = (value: number) => {
        return new Intl.NumberFormat('en-US', {
          style: 'currency',
          currency: 'USD',
          notation: 'compact',
          maximumFractionDigits: 1,
        }).format(value)
      }

      expect(formatCompactCurrency(1500000)).toBe('$1.5M')
      expect(formatCompactCurrency(1000000000)).toBe('$1B')
      expect(formatCompactCurrency(5500)).toBe('$5.5K')
    })
  })
})
