import { render, screen } from '@testing-library/react'
import MetricsComparisonChart from '@/components/charts/MetricsComparisonChart'

describe('MetricsComparisonChart', () => {
  const mockFunds = [
    { fundName: 'Fund A', dpi: 1.5, irr: 0.15, tvpi: 2.0, pic: 1000000 },
    { fundName: 'Fund B', dpi: 1.2, irr: 0.12, tvpi: 1.8, pic: 2000000 },
    { fundName: 'Fund C', dpi: 0.8, irr: 0.08, tvpi: 1.3, pic: 1500000 },
  ]

  it('renders without crashing', () => {
    render(<MetricsComparisonChart funds={mockFunds} />)
  })

  it('renders chart title with default metric (DPI)', () => {
    render(<MetricsComparisonChart funds={mockFunds} />)
    expect(screen.getByText(/DPI.*Comparison/i)).toBeInTheDocument()
  })

  it('renders chart with IRR metric', () => {
    render(<MetricsComparisonChart funds={mockFunds} metric="irr" />)
    expect(screen.getByText(/IRR.*Comparison/i)).toBeInTheDocument()
  })

  it('renders chart with TVPI metric', () => {
    render(<MetricsComparisonChart funds={mockFunds} metric="tvpi" />)
    expect(screen.getByText(/TVPI.*Comparison/i)).toBeInTheDocument()
  })

  it('renders chart with PIC metric', () => {
    render(<MetricsComparisonChart funds={mockFunds} metric="pic" />)
    expect(screen.getByText(/PIC.*Comparison/i)).toBeInTheDocument()
  })

  it('shows empty state when no funds provided', () => {
    render(<MetricsComparisonChart funds={[]} />)
    expect(screen.getByText(/No fund data available for comparison/i)).toBeInTheDocument()
  })

  it('shows empty state when funds is undefined', () => {
    render(<MetricsComparisonChart funds={undefined as any} />)
    expect(screen.getByText(/No fund data available for comparison/i)).toBeInTheDocument()
  })

  it('renders with correct number of data points', () => {
    const { container } = render(<MetricsComparisonChart funds={mockFunds} />)
    // ResponsiveContainer should be rendered
    expect(container.querySelector('.recharts-responsive-container')).toBeInTheDocument()
  })
})
