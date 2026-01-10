import { useState, useEffect, useRef } from 'react';
import { Link } from 'react-router-dom';
import { motion, useScroll, useTransform, useInView, AnimatePresence } from 'framer-motion';
import {
  Search,
  FileCheck,
  ClipboardCheck,
  ArrowRight,
  Shield,
  Zap,
  Building2,
  CheckCircle2,
  ChevronRight,
  BookOpen,
  Scale,
  FileText,
  Clock,
  Star,
  Menu,
  X,
  MapPin,
  Phone,
} from 'lucide-react';
import { ExploreWidget } from '../components/landing/ExploreWidget';

// Animated counter component
function AnimatedCounter({ end, duration = 2, suffix = '' }: { end: number; duration?: number; suffix?: string }) {
  const [count, setCount] = useState(0);
  const ref = useRef<HTMLSpanElement>(null);
  const isInView = useInView(ref, { once: true, margin: '-100px' });

  useEffect(() => {
    if (!isInView) return;

    let startTime: number;
    const animate = (timestamp: number) => {
      if (!startTime) startTime = timestamp;
      const progress = Math.min((timestamp - startTime) / (duration * 1000), 1);
      setCount(Math.floor(progress * end));
      if (progress < 1) requestAnimationFrame(animate);
    };
    requestAnimationFrame(animate);
  }, [isInView, end, duration]);

  return <span ref={ref}>{count.toLocaleString()}{suffix}</span>;
}

// Blueprint grid background component
function BlueprintGrid() {
  return (
    <div className="absolute inset-0 overflow-hidden pointer-events-none">
      {/* Main grid */}
      <div
        className="absolute inset-0 opacity-[0.03]"
        style={{
          backgroundImage: `
            linear-gradient(to right, #1e3a5f 1px, transparent 1px),
            linear-gradient(to bottom, #1e3a5f 1px, transparent 1px)
          `,
          backgroundSize: '40px 40px',
        }}
      />
      {/* Fine grid */}
      <div
        className="absolute inset-0 opacity-[0.015]"
        style={{
          backgroundImage: `
            linear-gradient(to right, #1e3a5f 1px, transparent 1px),
            linear-gradient(to bottom, #1e3a5f 1px, transparent 1px)
          `,
          backgroundSize: '8px 8px',
        }}
      />
      {/* Decorative circles */}
      <svg className="absolute top-20 right-20 w-64 h-64 text-slate-200/30" viewBox="0 0 100 100">
        <circle cx="50" cy="50" r="45" fill="none" stroke="currentColor" strokeWidth="0.5" strokeDasharray="4 2" />
        <circle cx="50" cy="50" r="35" fill="none" stroke="currentColor" strokeWidth="0.5" />
        <circle cx="50" cy="50" r="25" fill="none" stroke="currentColor" strokeWidth="0.5" strokeDasharray="2 4" />
      </svg>
      {/* Corner marks */}
      <div className="absolute top-8 left-8 w-16 h-16 border-l-2 border-t-2 border-slate-200/20" />
      <div className="absolute bottom-8 right-8 w-16 h-16 border-r-2 border-b-2 border-slate-200/20" />
    </div>
  );
}

// Navigation
function Navigation() {
  const [isScrolled, setIsScrolled] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  useEffect(() => {
    const handleScroll = () => setIsScrolled(window.scrollY > 20);
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  return (
    <>
      <motion.nav
        initial={{ y: -100 }}
        animate={{ y: 0 }}
        className={`fixed top-0 left-0 right-0 z-50 transition-all duration-300 ${
          isScrolled ? 'bg-white/90 backdrop-blur-xl shadow-lg shadow-slate-900/5' : 'bg-transparent'
        }`}
      >
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            {/* Logo */}
            <Link to="/" className="flex items-center gap-3 group">
              <div className="relative w-10 h-10 rounded-lg bg-gradient-to-br from-slate-800 to-slate-900 flex items-center justify-center overflow-hidden">
                <Building2 className="w-5 h-5 text-amber-400" />
                <div className="absolute inset-0 bg-gradient-to-t from-amber-500/20 to-transparent" />
              </div>
              <div className="flex flex-col">
                <span className="font-semibold text-slate-900 tracking-tight">CodeCheck</span>
                <span className="text-[10px] font-medium text-amber-600 tracking-widest uppercase">Calgary</span>
              </div>
            </Link>

            {/* Desktop Navigation */}
            <div className="hidden md:flex items-center gap-1">
              {['Features', 'Pricing', 'Standards', 'Blog'].map((item) => (
                <a
                  key={item}
                  href={`#${item.toLowerCase()}`}
                  className="px-4 py-2 text-sm font-medium text-slate-600 hover:text-slate-900 rounded-lg hover:bg-slate-100 transition-colors"
                >
                  {item}
                </a>
              ))}
            </div>

            {/* Auth Buttons */}
            <div className="hidden md:flex items-center gap-3">
              <Link
                to="/login"
                className="px-4 py-2 text-sm font-medium text-slate-600 hover:text-slate-900 transition-colors"
              >
                Sign in
              </Link>
              <Link
                to="/signup"
                className="px-5 py-2.5 text-sm font-semibold text-slate-900 bg-amber-400 hover:bg-amber-500 rounded-lg transition-all shadow-lg shadow-amber-500/20 hover:shadow-amber-500/30 hover:-translate-y-0.5"
              >
                Start Free Trial
              </Link>
            </div>

            {/* Mobile menu button */}
            <button
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="md:hidden p-2 rounded-lg hover:bg-slate-100"
            >
              {mobileMenuOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
            </button>
          </div>
        </div>
      </motion.nav>

      {/* Mobile menu */}
      <AnimatePresence>
        {mobileMenuOpen && (
          <motion.div
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            className="fixed inset-x-0 top-[72px] z-40 bg-white border-b border-slate-200 shadow-xl md:hidden"
          >
            <div className="p-6 space-y-4">
              {['Features', 'Pricing', 'Standards', 'Blog'].map((item) => (
                <a
                  key={item}
                  href={`#${item.toLowerCase()}`}
                  onClick={() => setMobileMenuOpen(false)}
                  className="block py-2 text-lg font-medium text-slate-700"
                >
                  {item}
                </a>
              ))}
              <div className="pt-4 border-t border-slate-100 space-y-3">
                <Link to="/login" className="block w-full text-center py-3 text-slate-600 font-medium">
                  Sign in
                </Link>
                <Link
                  to="/signup"
                  className="block w-full text-center py-3 bg-amber-400 text-slate-900 font-semibold rounded-lg"
                >
                  Start Free Trial
                </Link>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
}

// Hero Section
function HeroSection() {
  const { scrollY } = useScroll();
  const y = useTransform(scrollY, [0, 500], [0, 150]);

  return (
    <section className="relative min-h-screen flex items-center pt-20 overflow-hidden bg-gradient-to-b from-slate-50 to-white">
      <BlueprintGrid />

      {/* Gradient orbs */}
      <motion.div
        style={{ y }}
        className="absolute top-1/4 -left-32 w-96 h-96 bg-amber-400/10 rounded-full blur-3xl"
      />
      <motion.div
        style={{ y: useTransform(scrollY, [0, 500], [0, -100]) }}
        className="absolute bottom-1/4 -right-32 w-96 h-96 bg-teal-400/10 rounded-full blur-3xl"
      />

      <div className="relative max-w-7xl mx-auto px-6 py-20">
        <div className="grid lg:grid-cols-2 gap-12 items-center">
          {/* Left column - Text content */}
          <div className="text-center lg:text-left">
            {/* Badge */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.1 }}
              className="inline-flex items-center gap-2 px-4 py-2 bg-amber-50 border border-amber-200 rounded-full text-amber-700 text-sm font-medium mb-8"
            >
              <Star className="w-4 h-4 fill-amber-400 text-amber-400" />
              <span>Trusted by 500+ Calgary builders</span>
            </motion.div>

            {/* Main headline */}
            <motion.h1
              initial={{ opacity: 0, y: 30 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.2 }}
              className="text-4xl md:text-5xl lg:text-6xl font-bold text-slate-900 leading-[1.1] tracking-tight mb-6"
            >
              Get Your Calgary Permit{' '}
              <span className="relative inline-block">
                <span className="relative z-10 text-transparent bg-clip-text bg-gradient-to-r from-amber-500 to-amber-600">
                  Approved
                </span>
                <svg className="absolute -bottom-2 left-0 w-full" viewBox="0 0 200 12" fill="none">
                  <path d="M2 8 Q 100 2, 198 8" stroke="#f59e0b" strokeWidth="3" strokeLinecap="round" />
                </svg>
              </span>{' '}
              First Time
            </motion.h1>

            {/* Subheadline */}
            <motion.p
              initial={{ opacity: 0, y: 30 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.3 }}
              className="text-lg md:text-xl text-slate-600 max-w-xl mx-auto lg:mx-0 mb-8 leading-relaxed"
            >
              AI-powered compliance checking against NBC(AE) 2023, Calgary Land Use Bylaw,
              and <span className="font-medium text-slate-700">1,433+ SDAB decisions</span>.
            </motion.p>

            {/* CTA Buttons */}
            <motion.div
              initial={{ opacity: 0, y: 30 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.4 }}
              className="flex flex-col sm:flex-row items-center justify-center lg:justify-start gap-4 mb-10"
            >
              <Link
                to="/signup"
                className="group flex items-center gap-2 px-8 py-4 bg-slate-900 text-white font-semibold rounded-xl shadow-2xl shadow-slate-900/20 hover:shadow-slate-900/30 hover:-translate-y-1 transition-all"
              >
                Start Your Free Trial
                <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
              </Link>
              <Link
                to="/explore"
                className="group flex items-center gap-2 px-8 py-4 bg-white text-slate-700 font-semibold rounded-xl border-2 border-slate-200 hover:border-slate-300 hover:bg-slate-50 transition-all"
              >
                <Search className="w-5 h-5" />
                Full Explore
              </Link>
            </motion.div>

            {/* Trust indicators */}
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.6 }}
              className="flex flex-wrap items-center justify-center lg:justify-start gap-6 text-slate-400 text-sm"
            >
              <div className="flex items-center gap-2">
                <Shield className="w-4 h-4 text-teal-500" />
                <span>SOC 2 Compliant</span>
              </div>
              <div className="flex items-center gap-2">
                <Clock className="w-4 h-4 text-amber-500" />
                <span>Real-time Updates</span>
              </div>
              <div className="flex items-center gap-2">
                <Zap className="w-4 h-4 text-amber-500" />
                <span>Instant Analysis</span>
              </div>
            </motion.div>
          </div>

          {/* Right column - Interactive Explore Widget */}
          <div className="lg:pl-8">
            <ExploreWidget className="max-w-lg mx-auto lg:mx-0" />
          </div>
        </div>
      </div>
    </section>
  );
}

// Features Section
function FeaturesSection() {
  const features = [
    {
      icon: Search,
      title: 'Explore',
      subtitle: 'Search & Discover',
      description: 'Natural language search across NBC(AE) 2023, Calgary bylaws, and SDAB decisions. Find the exact clause you need in seconds.',
      color: 'amber',
      gradient: 'from-amber-500 to-orange-500',
      link: '/explore',
    },
    {
      icon: FileCheck,
      title: 'Guide',
      subtitle: 'Step-by-Step Compliance',
      description: 'Interactive checklists tailored to your project type. Never miss a requirement with guided permit preparation.',
      color: 'teal',
      gradient: 'from-teal-500 to-emerald-500',
      link: '/guide',
    },
    {
      icon: ClipboardCheck,
      title: 'Review',
      subtitle: 'AI-Powered Analysis',
      description: 'Upload your drawings and documents. Get instant compliance reports with specific code references and fix recommendations.',
      color: 'blue',
      gradient: 'from-blue-500 to-indigo-500',
      link: '/review',
    },
  ];

  return (
    <section id="features" className="py-32 bg-white relative overflow-hidden">
      <div className="absolute inset-0 bg-blueprint opacity-50" />

      <div className="relative max-w-7xl mx-auto px-6">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="text-center mb-20"
        >
          <span className="inline-block px-4 py-1.5 bg-slate-100 text-slate-600 text-sm font-medium rounded-full mb-4">
            Three Powerful Modes
          </span>
          <h2 className="text-4xl md:text-5xl font-bold text-slate-900 mb-6">
            Everything You Need to{' '}
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-amber-500 to-amber-600">
              Succeed
            </span>
          </h2>
          <p className="text-xl text-slate-600 max-w-2xl mx-auto">
            From initial research to final submission, CodeCheck guides you through every step of the permit process.
          </p>
        </motion.div>

        <div className="grid md:grid-cols-3 gap-8">
          {features.map((feature, index) => (
            <motion.div
              key={feature.title}
              initial={{ opacity: 0, y: 40 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: index * 0.1 }}
            >
              <Link
                to={feature.link}
                className="group block h-full p-8 rounded-2xl bg-white border border-slate-200 hover:border-slate-300 shadow-lg hover:shadow-xl transition-all duration-300 hover:-translate-y-2"
              >
                {/* Icon */}
                <div className={`inline-flex p-4 rounded-2xl bg-gradient-to-br ${feature.gradient} mb-6 shadow-lg`}>
                  <feature.icon className="w-8 h-8 text-white" />
                </div>

                {/* Content */}
                <div className="space-y-3">
                  <div className="flex items-center gap-2">
                    <h3 className="text-2xl font-bold text-slate-900">{feature.title}</h3>
                    <ChevronRight className="w-5 h-5 text-slate-400 group-hover:text-amber-500 group-hover:translate-x-1 transition-all" />
                  </div>
                  <p className="text-sm font-medium text-slate-500 uppercase tracking-wide">
                    {feature.subtitle}
                  </p>
                  <p className="text-slate-600 leading-relaxed">
                    {feature.description}
                  </p>
                </div>

                {/* Bottom decoration */}
                <div className="mt-8 pt-6 border-t border-slate-100">
                  <span className="text-sm font-medium text-amber-600 group-hover:text-amber-500">
                    Try {feature.title} Mode →
                  </span>
                </div>
              </Link>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}

// Statistics Section
function StatisticsSection() {
  const stats = [
    { value: 188019, label: 'Permits Analyzed', suffix: '+', icon: FileText },
    { value: 1433, label: 'SDAB Decisions', suffix: '', icon: Scale },
    { value: 420, label: 'NBC Requirements', suffix: '+', icon: BookOpen },
    { value: 98, label: 'First-Pass Approval Rate', suffix: '%', icon: CheckCircle2 },
  ];

  return (
    <section className="py-24 bg-slate-900 relative overflow-hidden">
      {/* Blueprint grid dark */}
      <div className="absolute inset-0 bg-blueprint-dark" />

      {/* Gradient overlay */}
      <div className="absolute inset-0 bg-gradient-to-r from-amber-500/5 via-transparent to-teal-500/5" />

      <div className="relative max-w-7xl mx-auto px-6">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="text-center mb-16"
        >
          <h2 className="text-3xl md:text-4xl font-bold text-white mb-4">
            Powered by Real Calgary Data
          </h2>
          <p className="text-lg text-slate-400 max-w-2xl mx-auto">
            Our AI is trained on years of permit history, SDAB decisions, and regulatory updates specific to Calgary.
          </p>
        </motion.div>

        <div className="grid grid-cols-2 md:grid-cols-4 gap-8">
          {stats.map((stat, index) => (
            <motion.div
              key={stat.label}
              initial={{ opacity: 0, y: 30 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: index * 0.1 }}
              className="text-center"
            >
              <div className="inline-flex p-3 rounded-xl bg-slate-800/50 mb-4">
                <stat.icon className="w-6 h-6 text-amber-400" />
              </div>
              <div className="text-4xl md:text-5xl font-bold text-white mb-2">
                <AnimatedCounter end={stat.value} suffix={stat.suffix} />
              </div>
              <div className="text-slate-400 font-medium">{stat.label}</div>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}

// Pricing Section
function PricingSection() {
  const plans = [
    {
      name: 'Free',
      price: 0,
      description: 'Get started with essential code search and permit guidance.',
      features: [
        '25 Explore searches/month',
        '3 Guide projects/month',
        'NBC(AE) 2023 access',
        'Basic compliance checklist',
        'Community support',
      ],
      cta: 'Get Started Free',
      highlighted: false,
      badge: null,
    },
    {
      name: 'Starter',
      price: 49,
      description: 'Perfect for individual contractors and small projects.',
      features: [
        'Unlimited Explore searches',
        '15 Guide projects/month',
        '5 Review analyses/month',
        'Email support',
        'Calgary Land Use Bylaw',
        'Export to PDF',
      ],
      cta: 'Start Free Trial',
      highlighted: false,
      badge: null,
    },
    {
      name: 'Professional',
      price: 199,
      description: 'For growing teams with multiple concurrent projects.',
      features: [
        'Everything in Starter',
        '50 Review analyses/month',
        'SDAB risk assessment',
        'API access',
        'Priority support',
        'Custom checklists',
        'Team collaboration (5 seats)',
      ],
      cta: 'Start Free Trial',
      highlighted: true,
      badge: 'Most Popular',
    },
    {
      name: 'Enterprise',
      price: null,
      description: 'For large builders and development companies.',
      features: [
        'Everything in Professional',
        'Unlimited Review analyses',
        'Dedicated account manager',
        'Custom integrations',
        'SLA guarantees',
        'On-premise deployment',
        'Training & onboarding',
      ],
      cta: 'Contact Sales',
      highlighted: false,
      badge: null,
    },
  ];

  return (
    <section id="pricing" className="py-32 bg-gradient-to-b from-white to-slate-50 relative">
      <BlueprintGrid />

      <div className="relative max-w-7xl mx-auto px-6">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="text-center mb-20"
        >
          <span className="inline-block px-4 py-1.5 bg-amber-100 text-amber-700 text-sm font-medium rounded-full mb-4">
            Simple, Transparent Pricing
          </span>
          <h2 className="text-4xl md:text-5xl font-bold text-slate-900 mb-6">
            Choose Your Plan
          </h2>
          <p className="text-xl text-slate-600 max-w-2xl mx-auto">
            Start free forever. Upgrade when you need more power.
          </p>
        </motion.div>

        <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6 items-start">
          {plans.map((plan, index) => (
            <motion.div
              key={plan.name}
              initial={{ opacity: 0, y: 40 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: index * 0.1 }}
              className={`relative rounded-2xl ${
                plan.highlighted
                  ? 'bg-slate-900 text-white shadow-2xl shadow-slate-900/20 lg:scale-105 z-10'
                  : plan.price === 0
                    ? 'bg-gradient-to-br from-teal-50 to-emerald-50 border-2 border-teal-200 shadow-lg'
                    : 'bg-white border border-slate-200 shadow-lg'
              }`}
            >
              {plan.badge && (
                <div className="absolute -top-4 left-1/2 -translate-x-1/2">
                  <span className="px-4 py-1 bg-amber-400 text-slate-900 text-sm font-semibold rounded-full whitespace-nowrap">
                    {plan.badge}
                  </span>
                </div>
              )}

              <div className="p-6">
                <h3 className={`text-xl font-bold ${plan.highlighted ? 'text-white' : 'text-slate-900'}`}>
                  {plan.name}
                </h3>
                <p className={`mt-2 text-sm ${plan.highlighted ? 'text-slate-400' : 'text-slate-600'}`}>
                  {plan.description}
                </p>

                <div className="mt-6 mb-6">
                  {plan.price === 0 ? (
                    <div className="flex items-baseline gap-1">
                      <span className="text-4xl font-bold text-teal-600">Free</span>
                      <span className="text-slate-500">forever</span>
                    </div>
                  ) : plan.price ? (
                    <div className="flex items-baseline gap-1">
                      <span className={`text-4xl font-bold ${plan.highlighted ? 'text-white' : 'text-slate-900'}`}>
                        ${plan.price}
                      </span>
                      <span className={plan.highlighted ? 'text-slate-400' : 'text-slate-500'}>/mo</span>
                    </div>
                  ) : (
                    <div className={`text-4xl font-bold ${plan.highlighted ? 'text-white' : 'text-slate-900'}`}>
                      Custom
                    </div>
                  )}
                </div>

                <ul className="space-y-3 mb-6">
                  {plan.features.map((feature) => (
                    <li key={feature} className="flex items-start gap-2">
                      <CheckCircle2 className={`w-4 h-4 flex-shrink-0 mt-0.5 ${
                        plan.highlighted ? 'text-amber-400' : plan.price === 0 ? 'text-teal-500' : 'text-teal-500'
                      }`} />
                      <span className={`text-sm ${plan.highlighted ? 'text-slate-300' : 'text-slate-600'}`}>
                        {feature}
                      </span>
                    </li>
                  ))}
                </ul>

                <button
                  className={`w-full py-3 px-6 rounded-xl font-semibold transition-all ${
                    plan.highlighted
                      ? 'bg-amber-400 text-slate-900 hover:bg-amber-500'
                      : plan.price === 0
                        ? 'bg-teal-600 text-white hover:bg-teal-700'
                        : 'bg-slate-900 text-white hover:bg-slate-800'
                  }`}
                >
                  {plan.cta}
                </button>
              </div>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}

// Standards Section
function StandardsSection() {
  const standards = [
    {
      category: 'National & Provincial Codes',
      items: [
        { name: 'NBC(AE) 2023', desc: 'National Building Code - Alberta Edition', badge: 'Primary' },
        { name: 'NECB 2020', desc: 'National Energy Code for Buildings', badge: null },
        { name: 'NPC 2020', desc: 'National Plumbing Code', badge: null },
        { name: 'CEC 2021', desc: 'Canadian Electrical Code', badge: null },
      ],
    },
    {
      category: 'Calgary Regulations',
      items: [
        { name: 'Land Use Bylaw 1P2007', desc: '68 land use districts', badge: 'Updated' },
        { name: 'Development Permits', desc: '188,019 historical decisions', badge: null },
        { name: 'Building Permits', desc: 'Requirements & processes', badge: null },
        { name: 'Safety Codes', desc: 'Local amendments', badge: null },
      ],
    },
    {
      category: 'Appeal Board Decisions',
      items: [
        { name: 'SDAB Decisions', desc: '1,433 appeal cases analyzed', badge: 'Exclusive' },
        { name: 'Precedent Database', desc: 'Searchable rulings', badge: null },
        { name: 'Risk Assessment', desc: 'Appeal likelihood scoring', badge: null },
        { name: 'Success Patterns', desc: 'Winning argument analysis', badge: null },
      ],
    },
    {
      category: 'Referenced Standards',
      items: [
        { name: 'CSA Standards', desc: '200+ referenced standards', badge: null },
        { name: 'ULC Standards', desc: 'Fire & safety testing', badge: null },
        { name: 'ASTM Standards', desc: 'Material specifications', badge: null },
        { name: 'STANDATA Bulletins', desc: 'Alberta interpretations', badge: null },
      ],
    },
  ];

  return (
    <section id="standards" className="py-32 bg-slate-50 relative overflow-hidden">
      <div className="absolute inset-0 bg-blueprint opacity-30" />

      <div className="relative max-w-7xl mx-auto px-6">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="text-center mb-20"
        >
          <span className="inline-block px-4 py-1.5 bg-slate-200 text-slate-700 text-sm font-medium rounded-full mb-4">
            Comprehensive Coverage
          </span>
          <h2 className="text-4xl md:text-5xl font-bold text-slate-900 mb-6">
            Standards & Codes We Review
          </h2>
          <p className="text-xl text-slate-600 max-w-3xl mx-auto">
            Every regulation, bylaw, and standard that affects your Calgary building project —
            analyzed and cross-referenced for complete compliance.
          </p>
        </motion.div>

        <div className="grid md:grid-cols-2 gap-8">
          {standards.map((section, sectionIndex) => (
            <motion.div
              key={section.category}
              initial={{ opacity: 0, y: 30 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: sectionIndex * 0.1 }}
              className="bg-white rounded-2xl border border-slate-200 shadow-lg overflow-hidden"
            >
              <div className="px-6 py-4 bg-slate-900">
                <h3 className="text-lg font-semibold text-white">{section.category}</h3>
              </div>
              <div className="divide-y divide-slate-100">
                {section.items.map((item) => (
                  <div key={item.name} className="px-6 py-4 hover:bg-slate-50 transition-colors">
                    <div className="flex items-start justify-between">
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="font-semibold text-slate-900">{item.name}</span>
                          {item.badge && (
                            <span className={`px-2 py-0.5 text-xs font-medium rounded ${
                              item.badge === 'Primary' ? 'bg-amber-100 text-amber-700' :
                              item.badge === 'Exclusive' ? 'bg-teal-100 text-teal-700' :
                              'bg-blue-100 text-blue-700'
                            }`}>
                              {item.badge}
                            </span>
                          )}
                        </div>
                        <p className="text-sm text-slate-500 mt-1">{item.desc}</p>
                      </div>
                      <ChevronRight className="w-5 h-5 text-slate-300" />
                    </div>
                  </div>
                ))}
              </div>
            </motion.div>
          ))}
        </div>

        {/* Bottom CTA */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="mt-16 text-center"
        >
          <p className="text-slate-600 mb-6">
            Plus <span className="font-semibold text-slate-900">4,293 refused permits</span> analyzed
            to help you avoid common mistakes.
          </p>
          <Link
            to="/explore"
            className="inline-flex items-center gap-2 px-6 py-3 bg-slate-900 text-white font-semibold rounded-xl hover:bg-slate-800 transition-colors"
          >
            <Search className="w-5 h-5" />
            Search the Database
          </Link>
        </motion.div>
      </div>
    </section>
  );
}

// CTA Section
function CTASection() {
  return (
    <section className="py-32 bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 relative overflow-hidden">
      {/* Decorative elements */}
      <div className="absolute inset-0">
        <div className="absolute top-0 left-1/4 w-96 h-96 bg-amber-500/10 rounded-full blur-3xl" />
        <div className="absolute bottom-0 right-1/4 w-96 h-96 bg-teal-500/10 rounded-full blur-3xl" />
      </div>

      <div className="relative max-w-4xl mx-auto px-6 text-center">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
        >
          <h2 className="text-4xl md:text-5xl font-bold text-white mb-6">
            Stop Guessing. Start{' '}
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-amber-400 to-amber-500">
              Building
            </span>
          </h2>
          <p className="text-xl text-slate-400 mb-10 max-w-2xl mx-auto">
            Join hundreds of Calgary builders who get their permits approved faster with CodeCheck.
            Start your free trial today — no credit card required.
          </p>

          <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
            <Link
              to="/signup"
              className="group flex items-center gap-2 px-8 py-4 bg-amber-400 text-slate-900 font-semibold rounded-xl shadow-2xl shadow-amber-500/20 hover:shadow-amber-500/30 hover:-translate-y-1 transition-all"
            >
              Start Your 14-Day Free Trial
              <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
            </Link>
            <a
              href="tel:+14035551234"
              className="flex items-center gap-2 px-8 py-4 text-white font-medium hover:text-amber-400 transition-colors"
            >
              <Phone className="w-5 h-5" />
              Talk to Sales
            </a>
          </div>

          <p className="mt-8 text-sm text-slate-500">
            Questions? Email us at{' '}
            <a href="mailto:hello@codecheck.calgary" className="text-amber-400 hover:underline">
              hello@codecheck.calgary
            </a>
          </p>
        </motion.div>
      </div>
    </section>
  );
}

// Footer
function Footer() {
  const footerLinks = {
    Product: ['Features', 'Pricing', 'API', 'Integrations', 'Changelog'],
    Resources: ['Documentation', 'Blog', 'Tutorials', 'Support', 'Status'],
    Company: ['About', 'Careers', 'Press', 'Contact', 'Partners'],
    Legal: ['Privacy', 'Terms', 'Security', 'Compliance'],
  };

  return (
    <footer className="bg-slate-900 border-t border-slate-800">
      <div className="max-w-7xl mx-auto px-6 py-16">
        <div className="grid grid-cols-2 md:grid-cols-5 gap-8">
          {/* Brand column */}
          <div className="col-span-2 md:col-span-1">
            <div className="flex items-center gap-3 mb-6">
              <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-slate-700 to-slate-800 flex items-center justify-center">
                <Building2 className="w-5 h-5 text-amber-400" />
              </div>
              <div>
                <span className="font-semibold text-white">CodeCheck</span>
                <span className="block text-[10px] text-amber-500 tracking-widest uppercase">Calgary</span>
              </div>
            </div>
            <p className="text-sm text-slate-400 mb-6">
              AI-powered building code compliance for Calgary construction professionals.
            </p>
            <div className="flex items-center gap-2 text-sm text-slate-500">
              <MapPin className="w-4 h-4" />
              <span>Calgary, Alberta</span>
            </div>
          </div>

          {/* Link columns */}
          {Object.entries(footerLinks).map(([category, links]) => (
            <div key={category}>
              <h4 className="font-semibold text-white mb-4">{category}</h4>
              <ul className="space-y-3">
                {links.map((link) => (
                  <li key={link}>
                    <a
                      href="#"
                      className="text-sm text-slate-400 hover:text-amber-400 transition-colors"
                    >
                      {link}
                    </a>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        {/* Bottom bar */}
        <div className="mt-16 pt-8 border-t border-slate-800 flex flex-col md:flex-row items-center justify-between gap-4">
          <p className="text-sm text-slate-500">
            © 2024 CodeCheck Calgary. All rights reserved.
          </p>
          <div className="flex items-center gap-6">
            <a href="#" className="text-slate-400 hover:text-white transition-colors">
              <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                <path d="M24 4.557c-.883.392-1.832.656-2.828.775 1.017-.609 1.798-1.574 2.165-2.724-.951.564-2.005.974-3.127 1.195-.897-.957-2.178-1.555-3.594-1.555-3.179 0-5.515 2.966-4.797 6.045-4.091-.205-7.719-2.165-10.148-5.144-1.29 2.213-.669 5.108 1.523 6.574-.806-.026-1.566-.247-2.229-.616-.054 2.281 1.581 4.415 3.949 4.89-.693.188-1.452.232-2.224.084.626 1.956 2.444 3.379 4.6 3.419-2.07 1.623-4.678 2.348-7.29 2.04 2.179 1.397 4.768 2.212 7.548 2.212 9.142 0 14.307-7.721 13.995-14.646.962-.695 1.797-1.562 2.457-2.549z"/>
              </svg>
            </a>
            <a href="#" className="text-slate-400 hover:text-white transition-colors">
              <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"/>
              </svg>
            </a>
            <a href="#" className="text-slate-400 hover:text-white transition-colors">
              <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                <path d="M19 0h-14c-2.761 0-5 2.239-5 5v14c0 2.761 2.239 5 5 5h14c2.762 0 5-2.239 5-5v-14c0-2.761-2.238-5-5-5zm-11 19h-3v-11h3v11zm-1.5-12.268c-.966 0-1.75-.79-1.75-1.764s.784-1.764 1.75-1.764 1.75.79 1.75 1.764-.783 1.764-1.75 1.764zm13.5 12.268h-3v-5.604c0-3.368-4-3.113-4 0v5.604h-3v-11h3v1.765c1.396-2.586 7-2.777 7 2.476v6.759z"/>
              </svg>
            </a>
          </div>
        </div>
      </div>
    </footer>
  );
}

// Main Landing Page Component
export function LandingPage() {
  return (
    <div className="min-h-screen">
      <Navigation />
      <main>
        <HeroSection />
        <FeaturesSection />
        <StatisticsSection />
        <PricingSection />
        <StandardsSection />
        <CTASection />
      </main>
      <Footer />
    </div>
  );
}

export default LandingPage;
