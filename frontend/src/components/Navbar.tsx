"use client";

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { Home, Wine, Bot, ShoppingCart, UserCircle } from 'lucide-react';

const Navbar = () => {
  const pathname = usePathname();

  const navItems = [
    { href: '/', label: 'Home', icon: Home },
    { href: '/browse-wines', label: 'Browse Wines', icon: Wine },
    { href: '/ai-sommelier', label: 'AI Sommelier', icon: Bot },
    { href: '/cart', label: 'Cart', icon: ShoppingCart },
    { href: '/account', label: 'Account', icon: UserCircle },
  ];

  return (
    <nav 
      className="fixed top-0 left-0 right-0 z-50 w-full bg-opacity-100 shadow-md"
      style={{ backgroundColor: 'var(--card-background)' }}
    >
      <ul className="flex items-center justify-around max-w-6xl mx-auto p-4">
        {navItems.map((item) => (
          <li key={item.href}>
            <Link
              href={item.href}
              className={`flex items-center px-4 py-2 rounded-md text-sm font-medium transition-colors
                ${pathname === item.href
                  ? 'bg-primary text-primary-foreground'
                  : 'text-secondary-foreground hover:bg-accent hover:text-accent-foreground'
                }
              `}
            >
              <item.icon className="mr-2 h-5 w-5" />
              {item.label}
            </Link>
          </li>
        ))}
      </ul>
    </nav>
  );
};

export default Navbar;
