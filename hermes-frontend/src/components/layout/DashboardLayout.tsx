import type { ReactNode } from "react";
import { AppNavigation } from "./AppNavigation";

interface DashboardLayoutProps {
    header?: ReactNode;
    children: ReactNode;
    sidebar?: ReactNode; // Right Sidebar (Metrics/Context)
}

export function DashboardLayout({ header, children, sidebar }: DashboardLayoutProps) {
    return (
        <div className="flex h-screen bg-background text-foreground font-sans overflow-hidden">
            {/* Left Navigation (Global) */}
            <AppNavigation />

            {/* Main Content Area */}
            <div className="flex-1 flex flex-col min-h-0 overflow-hidden relative">

                {/* Contextual Header (Optional) */}
                {header && (
                    <div className="shrink-0 z-40 px-6 pt-4">
                        {header}
                    </div>
                )}

                {/* Content Scroll Area */}
                <div className="flex-1 overflow-y-auto p-6 pt-2">
                    <div className="grid grid-cols-1 xl:grid-cols-12 gap-6 h-full pb-6">
                        {/* Main Workspace */}
                        <main className={`flex flex-col min-h-[600px] h-full ${sidebar ? 'xl:col-span-9' : 'xl:col-span-12'}`}>
                            {children}
                        </main>

                        {/* Right Sidebar (Contextual) */}
                        {sidebar && (
                            <aside className="xl:col-span-3 flex flex-col gap-4">
                                {sidebar}
                            </aside>
                        )}
                    </div>
                </div>

            </div>
        </div>
    );
}
