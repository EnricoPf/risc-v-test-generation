import json
import os
from pathlib import Path

class RiscVProfiles:
    def __init__(self):
        self.profiles = {}
        self.extensions = {}
        self.metadata = {}
        self.raw_data = None
        self.profiles_file_path = None
        self._load_profiles()
    
    def _load_profiles(self):
        """Load profiles and extensions from riscv-profiles.json"""
        profiles_file = Path(__file__).parent / "data" / "profiles" / "riscv-profiles.json"
        self.profiles_file_path = str(profiles_file)
        
        try:
            with open(profiles_file, 'r') as f:
                data = json.load(f)
                self.raw_data = data
                self.metadata = data.get('metadata', {})
                self.profiles = data.get('profiles', {})
                self.extensions = data.get('extensions', {})
        except Exception as e:
            print(f"Warning: Failed to load profiles from {profiles_file}: {e}")
    
    def get_profiles(self):
        """Get all available profiles"""
        return self.profiles
    
    def get_profile_details(self, profile_name):
        """Get details for a specific profile"""
        profile = self.profiles.get(profile_name)
        if not profile:
            return None
        
        return {
            "name": profile.get('description', ''),
            "description": profile.get('description', ''),
            "base": profile.get('base_isa', ''),
            "mandatory": profile.get('mandatory_extensions', []),
            "optional": profile.get('optional_extensions', []),
            "status": profile.get('status', ''),
            "typical_use": profile.get('typical_use', '')
        }
    
    def get_extension_details(self, extension_name):
        """Get details for a specific extension"""
        extension = self.extensions.get(extension_name)
        if not extension:
            return None
        
        return extension.get('description', '')
    
    def get_compatible_profiles(self, extensions):
        """Get all profiles that are compatible with the given extensions"""
        compatible_profiles = []
        
        for profile_name, profile in self.profiles.items():
            # Get all mandatory extensions for this profile
            mandatory_extensions = set(profile.get('mandatory_extensions', []))
            
            # Check if all mandatory extensions are present
            if mandatory_extensions.issubset(set(extensions)):
                compatible_profiles.append(profile_name)
        
        return compatible_profiles

    def get_raw_dataset(self):
        """Return the entire dataset exactly as in riscv-profiles.json (including metadata)."""
        if self.raw_data is not None:
            return self.raw_data
        # Fallback if raw_data was not loaded for some reason
        return {
            "metadata": self.metadata,
            "profiles": self.profiles,
            "extensions": self.extensions,
        }

    def get_profiles_file_path(self):
        """Return the path to the riscv-profiles.json file used for loading."""
        return self.profiles_file_path
    
    def save_extensions(self, filepath=None):
        """Save extensions to a JSON file"""
        if filepath is None:
            data_dir = Path(os.path.dirname(os.path.abspath(__file__))) / "data"
            filepath = data_dir / "extensions.json"
            
        # Create the directory if it doesn't exist
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        # Group extensions by category
        extension_data = {
            "base": {},
            "standard": {},
            "specialized": {},
            "supervisor": {},
            "hypervisor": {}
        }
        
        # Sort extensions into categories (simple heuristic)
        for ext_name, ext_desc in self.extensions.items():
            if ext_name.startswith("RV"):
                extension_data["base"][ext_name] = ext_desc
            elif ext_name.startswith("Z"):
                extension_data["specialized"][ext_name] = ext_desc
            elif ext_name.startswith("S"):
                extension_data["supervisor"][ext_name] = ext_desc
            elif len(ext_name) == 1:
                extension_data["standard"][ext_name] = ext_desc
            else:
                extension_data["standard"][ext_name] = ext_desc
        
        # Save to file
        with open(filepath, 'w') as f:
            json.dump(extension_data, f, indent=2)
    
    def save_profiles(self, filepath=None):
        """Save profiles to a JSON file"""
        if filepath is None:
            data_dir = Path(os.path.dirname(os.path.abspath(__file__))) / "data"
            filepath = data_dir / "profiles.json"
            
        # Create the directory if it doesn't exist
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        # Group profiles by category
        profile_data = {
            "application": {},
            "general_purpose": {},
            "integer_only": {},
            "embedded": {},
            "specialized": {},
            "classic": {}
        }
        
        # Sort profiles into categories (simple heuristic)
        for profile_name, profile in self.profiles.items():
            if profile_name.startswith("RVA"):
                profile_data["application"][profile_name] = profile
            elif profile_name.startswith("RVG"):
                profile_data["general_purpose"][profile_name] = profile
            elif profile_name.startswith("RVI"):
                profile_data["integer_only"][profile_name] = profile
            elif profile_name.startswith("RVE") or "E" in profile_name:
                profile_data["embedded"][profile_name] = profile
            elif profile_name.startswith("RVB") or profile_name.startswith("RVZ") or profile_name.startswith("RVP") or profile_name.startswith("RVV"):
                profile_data["specialized"][profile_name] = profile
            else:
                profile_data["classic"][profile_name] = profile
        
        # Save to file
        with open(filepath, 'w') as f:
            json.dump(profile_data, f, indent=2)
    
    def add_extension(self, name, description):
        """Add a new extension to the database"""
        self.extensions[name] = description
        
    def add_profile(self, name, profile_data):
        """Add a new profile to the database"""
        self.profiles[name] = profile_data
        
    def remove_extension(self, name):
        """Remove an extension from the database"""
        if name in self.extensions:
            del self.extensions[name]
            
    def remove_profile(self, name):
        """Remove a profile from the database"""
        if name in self.profiles:
            del self.profiles[name] 