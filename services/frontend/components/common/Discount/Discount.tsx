import * as React from 'react'

export interface DiscountCodeResults {
  data: string | null
}

function Discount() {
  const [data, setData] = React.useState<DiscountCodeResults | null>(null)
  const [isLoading, setLoading] = React.useState(false)
  const discountPath = process.env.NEXT_PUBLIC_DISCOUNTS_ROUTE

  function getRandomArbitrary(min: number, max: number) {
    return Math.floor(Math.random() * (max - min) + min)
  }

  function fetchDiscountCode() {
    setLoading(true) // Ensure the loading state is set before fetching

    // FIXED from Challenge 3: Removed ?limit=5 parameter since backend no longer supports it
    // The backend now returns all discounts without limit functionality
    fetch(`${discountPath}/discount`)
      .then((res) => {
        if (!res.ok) {
          // Handle HTTP errors explicitly
          throw new Error(`HTTP error! status: ${res.status}`)
        }
        return res.json()
      })
      .then((data) => {
        if (data && Array.isArray(data) && data.length > 0) {
          const index = getRandomArbitrary(0, data.length)
          setData(data[index]['code'])
        } else {
          throw new Error('No discount data found.')
        }
      })
      .catch((e) => {
        console.error('An error occurred while fetching the discount code:', e)
      })
      .finally(() => {
        setLoading(false) // Ensure loading state is updated
      })
  }

  React.useEffect(() => {
    setLoading(true)
    fetchDiscountCode()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  // FIXED from Challenge 3: Restored proper error handling
  // Previously this fallback case was removed, causing blank discount codes when API failed
  // Now properly shows "STOREDOG" as fallback when data is null
  return (
    <div className="flex flex-row justify-center py-4 bg-primary-2 text-white discount-wrapper">
      {isLoading ? (
        <span>GET FREE SHIPPING WITH DISCOUNT CODE</span>
      ) : !data ? (
        <span>
          GET FREE SHIPPING WITH DISCOUNT CODE <strong>STOREDOG</strong>
        </span>
      ) : (
        <span>
          GET FREE SHIPPING WITH DISCOUNT CODE &nbsp;{' '}
          <strong id="discount-code">{data}</strong>
        </span>
      )}
    </div>
  )
}

export default Discount
