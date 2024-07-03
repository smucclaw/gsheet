function myConfigFunction() {
    return ("this is a lightweight configuration control library that loads a particular Common Lib so we can select based on version for dev vs production.")
  }
  
  const PARENT_URL_HOST="https://prod.cclaw.legalese.com";
  const PARENT_URL_PORT="8090";
  
  function configLibDefaults () {
    return { parentUrlHost: PARENT_URL_HOST,
             parentUrlPort: PARENT_URL_PORT,
             devUrlHost: "https://cclaw.legalese.com",
             devUrlPort: "8090",
     }
  }