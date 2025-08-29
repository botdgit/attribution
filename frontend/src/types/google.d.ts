declare global {
  interface Window {
    google?: {
      accounts: {
        id: {
          initialize: (config: {
            client_id: string;
            callback: (response: google.accounts.id.CredentialResponse) => void;
          }) => void;
          prompt: () => void;
        };
      };
    };
  }
}

declare namespace google {
  namespace accounts {
    namespace id {
      interface CredentialResponse {
        credential: string;
        select_by: string;
      }
    }
  }
}

export {};