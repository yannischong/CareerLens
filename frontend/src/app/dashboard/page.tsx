import {
    redirect,
  } from "next/navigation";

  import {
    createClient,
  } from "@/lib/supabase/server";

  import DashboardClient
    from "./dashboard-client";


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
      redirect(
        "/login"
      );
    }


    return (
      <main className="min-h-screen bg-slate-50">

        <DashboardClient
          userEmail={
            user.email
            ?? ""
          }
        />

      </main>
    );
  }
