import React from 'react'
import { FiMoon, FiSun } from 'react-icons/fi'
import { useTheme } from 'next-themes'
import { Button } from './button'

interface NavbarProps {
  className?: string
  children?: React.ReactNode
}

interface NavbarSubComponentProps {
  children?: React.ReactNode
}

const NavbarBrand: React.FC<NavbarSubComponentProps> = ({ children }) => (
  <div className="flex items-center flex-shrink-0 mr-6">
    {children}
  </div>
)

const NavbarItems: React.FC<NavbarSubComponentProps> = ({ children }) => (
  <div className="flex-grow flex items-center w-auto">
    <div className="text-sm flex-grow"></div>
    <div>
      {children}
    </div>
  </div>
)

const Navbar = React.forwardRef<HTMLElement, NavbarProps>(
  ({ className = '', children }, ref) => {
    return (
      <nav ref={ref} className={`flex items-center justify-between flex-wrap bg-white dark:bg-black p-6 ${className}`}>
        {children}
      </nav>
    )
  }
)

Navbar.displayName = 'Navbar'

export const ThemeToggle: React.FC = () => {
  const { theme, setTheme } = useTheme()

  return (
    <Button
      variant="ghost"
      size="icon"
      onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}
      aria-label="Toggle theme"
    >
      {theme === 'dark' ? <FiSun className="h-5 w-5" /> : <FiMoon className="h-5 w-5" />}
    </Button>
  )
}

export { Navbar, NavbarBrand, NavbarItems }