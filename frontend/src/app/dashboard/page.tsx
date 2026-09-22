import {
  createClient,
} from "@/lib/supabase/server";

import DashboardClient
  from "./dashboard-client";

import GuestDashboard
  from "./guest-dashboard";


export default async function DashboardPage() {
  const supabase =
    await createClient();


  const {
    data: {
      user,
    },
  } =
    await supabase.auth
      .getUser();


  if (!user) {
    return (
      <GuestDashboard />
    );
  }


  return (
    <main className="min-h-screen bg-slate-50 dark:bg-slate-950">

      <DashboardClient
        userEmail={
          user.email
          ?? ""
        }
      />

    </main>
  );
}
