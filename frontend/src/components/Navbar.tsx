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
    <nav className="w-full max-w-6xl mb-8 bg-card-background shadow-md rounded-lg">
      <ul className="flex items-center justify-around p-4">
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
