# Frontend Test Suite

Comprehensive test suite for the Fund Performance Analysis System frontend built with Next.js 14, React, and TypeScript.

## Testing Stack

- **Jest** - Test runner and assertion library
- **React Testing Library** - Component testing utilities
- **@testing-library/jest-dom** - Custom Jest matchers for DOM
- **@testing-library/user-event** - User interaction simulation

## Test Structure

```
__tests__/
├── components/          # Component tests
│   ├── MetricsComparisonChart.test.tsx
│   └── ...
├── lib/                 # Utility function tests
│   └── utils.test.ts
└── README.md           # This file
```

## Running Tests

### Install Dependencies

```bash
cd frontend
npm install
```

### Run All Tests

```bash
npm test
```

### Run Tests in Watch Mode

```bash
npm run test:watch
```

### Run Tests with Coverage

```bash
npm run test:coverage
```

This generates a coverage report in `coverage/` directory.

### Run Specific Test File

```bash
npm test MetricsComparisonChart
```

### Run Tests with Verbose Output

```bash
npm test -- --verbose
```

## Writing Tests

### Component Test Example

```typescript
import { render, screen } from '@testing-library/react'
import MyComponent from '@/components/MyComponent'

describe('MyComponent', () => {
  it('renders correctly', () => {
    render(<MyComponent />)
    expect(screen.getByText('Expected Text')).toBeInTheDocument()
  })

  it('handles user interaction', async () => {
    const { user } = render(<MyComponent />)
    const button = screen.getByRole('button', { name: /click me/i })

    await user.click(button)

    expect(screen.getByText('Clicked!')).toBeInTheDocument()
  })
})
```

### Testing with React Query

For components using `@tanstack/react-query`:

```typescript
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render } from '@testing-library/react'

const createTestQueryClient = () => new QueryClient({
  defaultOptions: {
    queries: { retry: false },
    mutations: { retry: false },
  },
})

const renderWithQueryClient = (ui: React.ReactElement) => {
  const testQueryClient = createTestQueryClient()
  return render(
    <QueryClientProvider client={testQueryClient}>
      {ui}
    </QueryClientProvider>
  )
}

// Usage
it('fetches and displays data', async () => {
  renderWithQueryClient(<MyComponent />)

  await waitFor(() => {
    expect(screen.getByText('Data loaded')).toBeInTheDocument()
  })
})
```

### Testing Async Operations

```typescript
import { waitFor } from '@testing-library/react'

it('loads data asynchronously', async () => {
  render(<AsyncComponent />)

  // Wait for loading state to finish
  await waitFor(() => {
    expect(screen.queryByText('Loading...')).not.toBeInTheDocument()
  })

  expect(screen.getByText('Data loaded')).toBeInTheDocument()
})
```

### Testing User Interactions

```typescript
import userEvent from '@testing-library/user-event'

it('handles form submission', async () => {
  const user = userEvent.setup()
  render(<MyForm />)

  const input = screen.getByLabelText('Name')
  const submitButton = screen.getByRole('button', { name: /submit/i })

  await user.type(input, 'John Doe')
  await user.click(submitButton)

  expect(screen.getByText('Form submitted')).toBeInTheDocument()
})
```

### Mocking API Calls

```typescript
// Mock fetch globally
global.fetch = jest.fn(() =>
  Promise.resolve({
    ok: true,
    json: async () => ({ data: 'mocked' }),
  })
) as jest.Mock

// Or mock per test
it('fetches data', async () => {
  jest.spyOn(global, 'fetch').mockResolvedValueOnce({
    ok: true,
    json: async () => [{ id: 1, name: 'Fund A' }],
  } as Response)

  // Your test logic
})
```

## Test Coverage Goals

Target coverage metrics:
- **Statements**: >80%
- **Branches**: >75%
- **Functions**: >80%
- **Lines**: >80%

### View Coverage Report

After running `npm run test:coverage`:

```bash
# Open HTML report
open coverage/lcov-report/index.html
```

## Common Testing Patterns

### 1. Testing Chart Components (Recharts)

```typescript
import { render } from '@testing-library/react'
import CashFlowChart from '@/components/charts/CashFlowChart'

it('renders chart', () => {
  const mockData = [
    { date: '2023-01', amount: 1000 },
    { date: '2023-02', amount: 2000 },
  ]

  const { container } = render(<CashFlowChart data={mockData} />)

  // Recharts uses ResponsiveContainer
  expect(container.querySelector('.recharts-responsive-container')).toBeInTheDocument()
})
```

### 2. Testing Next.js Links and Navigation

```typescript
// Navigation is mocked in jest.setup.js
import { useRouter } from 'next/navigation'

it('navigates on button click', async () => {
  const user = userEvent.setup()
  const router = useRouter()

  render(<MyComponent />)

  await user.click(screen.getByText('Go to Page'))

  expect(router.push).toHaveBeenCalledWith('/target-page')
})
```

### 3. Testing Loading States

```typescript
it('shows loading state', () => {
  render(<MyComponent isLoading={true} />)
  expect(screen.getByText('Loading...')).toBeInTheDocument()
})

it('shows content after loading', () => {
  const { rerender } = render(<MyComponent isLoading={true} />)

  rerender(<MyComponent isLoading={false} data={mockData} />)

  expect(screen.queryByText('Loading...')).not.toBeInTheDocument()
  expect(screen.getByText('Content')).toBeInTheDocument()
})
```

### 4. Testing Error States

```typescript
it('displays error message', () => {
  render(<MyComponent error="Something went wrong" />)
  expect(screen.getByText('Something went wrong')).toBeInTheDocument()
})
```

## Best Practices

1. **Test User Behavior, Not Implementation**
   - Focus on what users see and do
   - Avoid testing internal state or implementation details

2. **Use Accessible Queries**
   - Prefer `getByRole`, `getByLabelText`, `getByText`
   - Avoid `getByTestId` unless necessary

3. **Keep Tests Isolated**
   - Each test should be independent
   - Clean up after each test (handled automatically by RTL)

4. **Use Descriptive Test Names**
   ```typescript
   // Good
   it('displays error message when API call fails')

   // Bad
   it('test 1')
   ```

5. **Mock External Dependencies**
   - Mock API calls
   - Mock external libraries when necessary
   - Use jest.mock() for module mocking

6. **Test Accessibility**
   ```typescript
   it('has accessible form labels', () => {
     render(<MyForm />)
     expect(screen.getByLabelText('Email')).toBeInTheDocument()
   })
   ```

## Debugging Tests

### View Rendered HTML

```typescript
import { render, screen } from '@testing-library/react'

it('debugs component', () => {
  const { debug } = render(<MyComponent />)

  // Print entire DOM
  debug()

  // Print specific element
  debug(screen.getByRole('button'))
})
```

### Check Available Queries

```typescript
screen.logTestingPlaygroundURL() // Opens Testing Playground
```

## Continuous Integration

### GitHub Actions Example

```yaml
name: Frontend Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v2

    - name: Setup Node.js
      uses: actions/setup-node@v2
      with:
        node-version: '18'

    - name: Install dependencies
      run: |
        cd frontend
        npm ci

    - name: Run tests
      run: |
        cd frontend
        npm test -- --coverage

    - name: Upload coverage
      uses: codecov/codecov-action@v2
      with:
        directory: ./frontend/coverage
```

## Troubleshooting

### "Cannot find module" Errors

Ensure `moduleNameMapper` in `jest.config.js` matches your `tsconfig.json` paths:

```javascript
moduleNameMapper: {
  '^@/(.*)$': '<rootDir>/$1',
}
```

### "window is not defined" Errors

Make sure you're using `jest-environment-jsdom`:

```javascript
// jest.config.js
testEnvironment: 'jest-environment-jsdom'
```

### Recharts Warnings

Recharts may show warnings in tests. To suppress:

```typescript
beforeAll(() => {
  jest.spyOn(console, 'warn').mockImplementation(() => {})
})

afterAll(() => {
  jest.restoreAllMocks()
})
```

## Resources

- [React Testing Library Docs](https://testing-library.com/react)
- [Jest Documentation](https://jestjs.io/docs/getting-started)
- [Common Testing Patterns](https://kentcdodds.com/blog/common-mistakes-with-react-testing-library)
- [Testing Playground](https://testing-playground.com/)

## Next Steps

1. Add more component tests for:
   - `CashFlowChart`
   - `FundPerformanceChart`
   - Fund detail pages
   - Comparison page

2. Add integration tests for:
   - Complete user workflows
   - Form submissions
   - API interactions

3. Set up E2E tests with Playwright or Cypress

4. Configure code coverage thresholds in Jest config
