import React, { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { auth } from "@/firebase";
import { onAuthStateChanged, signOut } from "firebase/auth";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from "@/components/ui/dropdown-menu";

export default function FirebaseAuth() {
	const [user, setUser] = useState(null);
	const navigate = useNavigate();

	useEffect(() => onAuthStateChanged(auth, setUser), []);

	async function handleLogout() {
		try {
			await signOut(auth);
			navigate("/");
		} catch (err) {
			console.error("Sign out failed", err);
		}
	}

	// If signed in show avatar + dropdown, otherwise show Login / Register links
	if (user) {
		const display = user.displayName || user.email || "User";
		return (
			<DropdownMenu>
				<DropdownMenuTrigger asChild>
					<Button variant="ghost" size="sm" className="rounded-full">
						<Avatar>
							<AvatarFallback>{(display || "U")[0].toUpperCase()}</AvatarFallback>
						</Avatar>
					</Button>
				</DropdownMenuTrigger>
				<DropdownMenuContent align="end">
					<DropdownMenuItem asChild>
						<Link to="/settings">Settings</Link>
					</DropdownMenuItem>
					<DropdownMenuItem onClick={handleLogout}>Log out</DropdownMenuItem>
				</DropdownMenuContent>
			</DropdownMenu>
		);
	}

	return (
		<div className="flex items-center space-x-2">
			<Link to="/login">
				<Button variant="ghost" size="default">Log in</Button>
			</Link>
			<Link to="/register">
				<Button variant="default" size="default">Register</Button>
			</Link>
		</div>
	);
}
