"use client";

import Link from 'next/link';
import { usePathname } from 'next/navigation';

const Navbar = () => {
  const pathname = usePathname();

  const navItems = [
    { href: '/', label: 'Home' },
    { href: '/browse-wines', label: 'Browse Wines' },
    { href: '/ai-sommelier', label: 'AI Sommelier' },
    { href: '/cart', label: 'Cart' },
    { href: '/account', label: 'Account' },
  ];

  return (
    <nav className="fixed top-0 left-0 right-0 z-50 w-full bg-card-background shadow-md">
      <ul className="flex items-center justify-around max-w-6xl mx-auto p-4">
        {navItems.map((item) => (
          <li key={item.href}>
            <Link
              href={item.href}
              className={`px-4 py-2 rounded-md text-sm font-medium transition-colors
                ${pathname === item.href
                  ? 'bg-primary text-primary-foreground'
                  : 'text-secondary-foreground hover:bg-accent hover:text-accent-foreground'
                }
              `}
            >
              {item.label}
            </Link>
          </li>
        ))}
      </ul>
    </nav>
  );
};

export default Navbar;
