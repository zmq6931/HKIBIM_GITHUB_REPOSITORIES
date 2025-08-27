import streamlit as st
import requests
import json
import pandas as pd

# Custom CSS for README container height
st.markdown("""
<style>
    .stContainer {
        height: 1000px !important;
        overflow-y: auto !important;
    }
</style>
""", unsafe_allow_html=True)

token = st.secrets["github_classic_token_test001"]
userName="HKIBIMTechnical"
change_name_code=st.secrets["change_name_code"]
#region function
def get_all_repositories(token, username=None):
    """
    Get all repositories for the authenticated user or a specific username.
    
    Args:
        token (str): GitHub personal access token
        username (str, optional): Specific username to get repositories for. 
                                 If None, gets repositories for the authenticated user.
    
    Returns:
        list: List of dictionaries containing repository information
              Each dict has 'name', 'url', 'html_url', 'clone_url', 'ssh_url'
    
    Raises:
        Exception: If the API request fails
    """
    headers = {
        'Authorization': f'token {token}',
        'Accept': 'application/vnd.github.v3+json'
    }
    
    # Determine the API endpoint
    if username:
        # Get repositories for a specific user
        url = f'https://api.github.com/users/{username}/repos'
    else:
        # Get repositories for the authenticated user
        url = 'https://api.github.com/user/repos'
    
    repositories = []
    page = 1
    per_page = 100  # Maximum allowed by GitHub API
    
    try:
        while True:
            params = {
                'page': page,
                'per_page': per_page,
                'sort': 'updated',  # Sort by last updated
                'direction': 'desc'  # Most recent first
            }
            
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            
            page_repos = response.json()
            
            # If no more repositories, break
            if not page_repos:
                break
            
            # Process repositories on this page
            for repo in page_repos:
                repo_info = {
                    'name': repo['name'],
                    'url': repo['url'],  # API URL
                    'html_url': repo['html_url'],  # Web page URL
                    'clone_url': repo['clone_url'],  # HTTPS clone URL
                    'ssh_url': repo['ssh_url'],  # SSH clone URL
                    'description': repo.get('description', ''),
                    'language': repo.get('language', ''),
                    'private': repo['private'],
                    'fork': repo['fork'],
                    'stars': repo['stargazers_count'],
                    'forks': repo['forks_count'],
                    'updated_at': repo['updated_at']
                }
                repositories.append(repo_info)
            
            # Check if we've reached the last page
            if len(page_repos) < per_page:
                break
            
            page += 1
            
        return repositories
        
    except requests.exceptions.RequestException as e:
        raise Exception(f"Failed to fetch repositories: {str(e)}")
    except Exception as e:
        raise Exception(f"Error processing repositories: {str(e)}")
def rename_repository(token, username, old_repository_name, new_repository_name):
    """
    Rename a GitHub repository.
    
    Args:
        token (str): GitHub personal access token with repo scope
        username (str): GitHub username (owner of the repository)
        old_repository_name (str): Current name of the repository
        new_repository_name (str): New name for the repository
    
    Returns:
        dict: Repository rename information including new URLs and details
        
    Raises:
        Exception: If the repository rename fails
    """
    headers = {
        'Authorization': f'token {token}',
        'Accept': 'application/vnd.github.v3+json'
    }
    
    # API endpoint for renaming repository
    url = f'https://api.github.com/repos/{username}/{old_repository_name}'
    
    # Repository rename data
    data = {
        'name': new_repository_name
    }
    
    try:
        # First check if the old repository exists
        check_response = requests.get(url, headers=headers)
        if check_response.status_code == 404:
            raise Exception(f"Repository '{old_repository_name}' not found")
        elif check_response.status_code != 200:
            check_response.raise_for_status()
        
        # Check if the new name is already taken
        new_url = f'https://api.github.com/repos/{username}/{new_repository_name}'
        new_check_response = requests.get(new_url, headers=headers)
        if new_check_response.status_code == 200:
            raise Exception(f"Repository name '{new_repository_name}' is already taken")
        
        # Make the PATCH request to rename the repository
        response = requests.patch(url, headers=headers, json=data)
        
        if response.status_code == 200:
            # Repository successfully renamed
            result = response.json()
            
            return {
                'status': 'success',
                'action': 'renamed',
                'old_name': old_repository_name,
                'new_name': new_repository_name,
                'full_name': result.get('full_name', ''),
                'html_url': result.get('html_url', ''),
                'clone_url': result.get('clone_url', ''),
                'ssh_url': result.get('ssh_url', ''),
                'private': result.get('private', False),
                'description': result.get('description', ''),
                'created_at': result.get('created_at', ''),
                'updated_at': result.get('updated_at', ''),
                'message': f"Repository '{old_repository_name}' successfully renamed to '{new_repository_name}'"
            }
        elif response.status_code == 422:
            raise Exception(f"Invalid repository name '{new_repository_name}' or name already exists")
        elif response.status_code == 403:
            raise Exception("Insufficient permissions. Token needs 'repo' scope or you don't have access to this repository")
        elif response.status_code == 401:
            raise Exception("Authentication failed. Check your token and permissions")
        else:
            raise Exception(f"Failed to rename repository. Status code: {response.status_code}")
            
    except requests.exceptions.RequestException as e:
        raise Exception(f"Failed to rename repository: {str(e)}")
    except Exception as e:
        raise Exception(f"Error renaming repository: {str(e)}")
def get_fileInfo_content(token, username, repository_Name, file_path="README.md", branch="main"):
    """
    Get file content or directory listing from a GitHub repository.
    file content include file name, path, content, size, sha, url, html_url, download_url, encoding.
    directory listing include file name, path, type, size, sha, url, html_url, download_url.
    current file README.md is under root folder, you can set your own file path.
    if file under folder, file path should be "folder/file.ext" for example.
    
    Args:
        token (str): GitHub personal access token
        username (str): GitHub username (owner of the repository)
        repository_Name (str): Name of the repository
        file_path (str): Path to the file or directory (empty string for root)
        branch (str): Branch name (default: "main")
    
    Returns:
        dict: File content or directory listing information
        
    Raises:
        Exception: If the file retrieval fails
    """
    headers = {
        'Authorization': f'token {token}',
        'Accept': 'application/vnd.github.v3+json'
    }
    
    # API endpoint for getting repository contents
    url = f'https://api.github.com/repos/{username}/{repository_Name}/contents/{file_path}'
    
    # Add branch parameter if specified
    if branch:
        url += f'?ref={branch}'
    
    try:
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            content_data = response.json()
            
            # Check if it's a file or directory
            if isinstance(content_data, dict):
                # Single file
                if content_data.get('type') == 'file':
                    # Decode content if it's encoded
                    content = content_data.get('content', '')
                    encoding = content_data.get('encoding', '')
                    
                    if encoding == 'base64':
                        import base64
                        try:
                            content = base64.b64decode(content).decode('utf-8')
                        except:
                            content = content_data.get('content', '')
                    
                    return {
                        'type': 'file',
                        'name': content_data.get('name', ''),
                        'path': content_data.get('path', ''),
                        'content': content,
                        'size': content_data.get('size', 0),
                        'sha': content_data.get('sha', ''),
                        'url': content_data.get('url', ''),
                        'html_url': content_data.get('html_url', ''),
                        'download_url': content_data.get('download_url', ''),
                        'encoding': encoding
                    }
                elif content_data.get('type') == 'dir':
                    # Directory - return list of files
                    return {
                        'type': 'directory',
                        'path': content_data.get('path', ''),
                        'files': content_data
                    }
                else:
                    return content_data
            elif isinstance(content_data, list):
                # Directory listing
                files = []
                for item in content_data:
                    file_info = {
                        'name': item.get('name', ''),
                        'path': item.get('path', ''),
                        'type': item.get('type', ''),  # 'file' or 'dir'
                        'size': item.get('size', 0),
                        'sha': item.get('sha', ''),
                        'url': item.get('url', ''),
                        'html_url': item.get('html_url', ''),
                        'download_url': item.get('download_url', '')
                    }
                    files.append(file_info)
                
                return {
                    'type': 'directory',
                    'path': file_path if file_path else 'root',
                    'files': files
                }
            else:
                return content_data
                
        elif response.status_code == 404:
            raise Exception(f"File or directory '{file_path}' not found in repository '{repository_Name}'")
        elif response.status_code == 403:
            raise Exception("Insufficient permissions or repository is private")
        elif response.status_code == 401:
            raise Exception("Authentication failed. Check your token and permissions")
        else:
            raise Exception(f"Failed to get file content. Status code: {response.status_code}")
            
    except requests.exceptions.RequestException as e:
        raise Exception(f"Failed to get file content: {str(e)}")
    except Exception as e:
        raise Exception(f"Error getting file content: {str(e)}")
def get_file_content_string(token, username, repository_Name, file_path="README.md", branch="main"):
    """
    Get content of a specific file from a GitHub repository.
    current file README.md is under root folder, you can set your own file path.
    if file under folder, file path should be "folder/file.ext" for example.
    Args:
        token (str): GitHub personal access token
        username (str): GitHub username (owner of the repository)
        repository_Name (str): Name of the repository
        file_path (str): Path to the specific file
        branch (str): Branch name (default: "main")
    
    Returns:
        str: File content as string
        
    Raises:
        Exception: If the file retrieval fails
    """
    result = get_fileInfo_content(token, username, repository_Name, file_path, branch)
    
    if result.get('type') == 'file':
        return result.get('content', '')
    else:
        raise Exception(f"Path '{file_path}' is not a file")
def check_file_or_folder_exists(token, username, repository_Name, file_path="README.md", branch="main"):
    """
    Check if a file or folder exists in a GitHub repository.
    current file README.md is under root folder, you can set your own file path.
    if file under folder, file path should be "folder/file.ext" for example.
    
    Args:
        token (str): GitHub personal access token
        username (str): GitHub username (owner of the repository)
        repository_Name (str): Name of the repository
        file_path (str): Path to the file or folder to check
        branch (str): Branch name (default: "main")
    
    Returns:
        dict: Existence status and type information
            {
                'exists': bool,
                'type': str,  # 'file', 'directory', or 'unknown'
                'path': str,
                'name': str,
                'size': int,
                'sha': str
            }
        
    Raises:
        Exception: If the check fails
    """
    headers = {
        'Authorization': f'token {token}',
        'Accept': 'application/vnd.github.v3+json'
    }
    
    # API endpoint for checking repository contents
    url = f'https://api.github.com/repos/{username}/{repository_Name}/contents/{file_path}'
    
    # Add branch parameter if specified
    if branch:
        url += f'?ref={branch}'
    
    try:
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            content_data = response.json()
            
            # File or directory exists
            if isinstance(content_data, dict):
                item_type = content_data.get('type', 'unknown')
                return {
                    'exists': True,
                    'type': item_type,  # 'file' or 'dir'
                    'path': content_data.get('path', ''),
                    'name': content_data.get('name', ''),
                    'size': content_data.get('size', 0),
                    'sha': content_data.get('sha', ''),
                    'html_url': content_data.get('html_url', ''),
                    'download_url': content_data.get('download_url', '')
                }
            elif isinstance(content_data, list):
                # This shouldn't happen for a specific path, but handle it
                return {
                    'exists': True,
                    'type': 'directory',
                    'path': file_path,
                    'name': file_path.split('/')[-1] if '/' in file_path else file_path,
                    'size': 0,
                    'sha': '',
                    'html_url': '',
                    'download_url': ''
                }
            else:
                return {
                    'exists': True,
                    'type': 'unknown',
                    'path': file_path,
                    'name': file_path.split('/')[-1] if '/' in file_path else file_path,
                    'size': 0,
                    'sha': '',
                    'html_url': '',
                    'download_url': ''
                }
                
        elif response.status_code == 404:
            # File or directory does not exist
            return {
                'exists': False,
                'type': 'none',
                'path': file_path,
                'name': file_path.split('/')[-1] if '/' in file_path else file_path,
                'size': 0,
                'sha': '',
                'html_url': '',
                'download_url': ''
            }
        elif response.status_code == 403:
            raise Exception("Insufficient permissions or repository is private")
        elif response.status_code == 401:
            raise Exception("Authentication failed. Check your token and permissions")
        else:
            raise Exception(f"Failed to check file existence. Status code: {response.status_code}")
            
    except requests.exceptions.RequestException as e:
        raise Exception(f"Failed to check file existence: {str(e)}")
    except Exception as e:
        raise Exception(f"Error checking file existence: {str(e)}")




#endregion





st.set_page_config(layout="wide")

# Add custom CSS for responsive table with dynamic border colors
st.markdown("""
<style>
    .repo-table {
        width: 100%;
        border-collapse: collapse;
        margin: 20px 0;
        font-family: Arial, sans-serif;
    }
    
    .repo-table th {
        background-color: var(--background-color, #f0f2f6);
        color: var(--text-color, #262730);
        padding: 12px;
        text-align: left;
        font-weight: bold;
        border: 2px solid var(--border-color, #262730);
    }
    
    .repo-table td {
        padding: 12px;
        border: 1px solid var(--border-color, #262730);
        vertical-align: top;
    }
    
    .repo-table tr:nth-child(even) {
        background-color: var(--alternate-row-color, rgba(151, 166, 195, 0.15));
    }
    
    .repo-table tr:hover {
        background-color: var(--hover-color, rgba(151, 166, 195, 0.25));
    }
    
    .rename-button {
        background-color: #ff6b6b;
        color: white;
        border: none;
        padding: 8px 16px;
        border-radius: 4px;
        cursor: pointer;
        font-size: 14px;
        transition: background-color 0.3s;
    }
    
    .rename-button:hover {
        background-color: #ff5252;
    }
    
    .rename-button:disabled {
        background-color: #ccc;
        cursor: not-allowed;
    }
    
    .url-cell {
        max-width: 300px;
        word-wrap: break-word;
        overflow-wrap: break-word;
    }
    
    .name-cell {
        font-weight: bold;
        color: var(--accent-color, #ff6b6b);
    }
    
    /* Dark mode detection and dynamic colors */
    @media (prefers-color-scheme: dark) {
        :root {
            --border-color: #ffffff;
            --background-color: #1e1e1e;
            --text-color: #ffffff;
            --alternate-row-color: rgba(255, 255, 255, 0.05);
            --hover-color: rgba(255, 255, 255, 0.1);
            --accent-color: #ff6b6b;
        }
    }
    
    /* Light mode (default) */
    :root {
        --border-color: #262730;
        --background-color: #f0f2f6;
        --text-color: #262730;
        --alternate-row-color: rgba(151, 166, 195, 0.15);
        --hover-color: rgba(151, 166, 195, 0.25);
        --accent-color: #ff6b6b;
    }
</style>
""", unsafe_allow_html=True)

st.title("HKIBIM Github Repositories")

# Get repositories
repos = get_all_repositories(token, userName)

# Create a container for the table
container = st.container()

# Create a proper table using Streamlit's native table functionality
# First, create the data for the table
table_data = []
for i, repo in enumerate(repos):
    table_data.append({
        "Name": repo['name'],
        "URL": repo['html_url'],
        "Index": i
    })





# Interactive dataframe with click functionality
st.markdown("### Repository Table")

# Container for Repository Table
with st.container():
    st.markdown("**📊 Repository List**")
    # Create dataframe without index column
    df_display = pd.DataFrame(table_data)
    
    # Use st.data_editor for interactive functionality
    edited_df = st.data_editor(
        df_display,
        use_container_width=True,
        hide_index=True,
        key="interactive_repo_dataframe"
    )



# Create rename functionality below the table
st.markdown("### Rename Repository")

# Add change name code input
change_name_input = st.text_input(
    "Change Name Code:",
    type="password",
    help="Enter the change name code to enable repository renaming",
    key="change_name_code_input"
)

selected_repo = st.selectbox(
    "Select repository to rename:",
    options=[repo['name'] for repo in repos],
    key="repo_selector"
)

if selected_repo:
    new_name = st.text_input(
        f"Enter new name for '{selected_repo}':",
        value=selected_repo,
        key="new_name_input"
    )
    
    col1, col2 = st.columns([1, 4])
    with col1:
        # Check if change name code is correct
        if change_name_input == change_name_code:
            if st.button("Rename Repository", type="primary"):
                if new_name and new_name != selected_repo:
                    try:
                        result = rename_repository(token, userName, selected_repo, new_name)
                        if result['status'] == 'success':
                            st.success(f"Repository renamed successfully from '{selected_repo}' to '{new_name}'")
                            st.rerun()
                        else:
                            st.error(f"Failed to rename repository: {result.get('message', 'Unknown error')}")
                    except Exception as e:
                        st.error(f"Error renaming repository: {str(e)}")
                else:
                    st.warning("Please enter a different name")
        else:
            # Show disabled button when code is incorrect
            st.button("Rename Repository", type="primary", disabled=True)
            if change_name_input:
                st.error("❌ Incorrect change name code. Please enter the correct code to enable renaming.")
            else:
                st.info("ℹ️ Please enter the change name code to enable repository renaming.")
    
    with col2:
        st.info(f"Current repository: {selected_repo}")

# Add a note about the table
st.info("The repositories are now displayed in a proper table format instead of columns.")

# Repository Selection and README Display
st.divider()
st.markdown("### 🔍 Repository Selection")
selected_repo_name = st.selectbox(
    "Select repository to view README:",
    options=[repo['name'] for repo in repos],
    key="repo_selector_for_readme"
)

# Show README content for selected repository
if selected_repo_name:
    st.markdown(f"---")
    st.markdown(f"### 📖 README.md for {selected_repo_name}")
    
    # Check if README.md exists and get content
    try:
        readme_content = get_file_content_string(token, userName, selected_repo_name, "README.md")
        if readme_content:
            st.markdown("**Content:**")
            st.markdown("---")
            
            # Container for README content with fixed height
            with st.container( height=600):
                st.markdown(readme_content)
                st.markdown("---")
        else:
            st.warning("README.md file exists but is empty")
    except Exception as e:
        if "not found" in str(e).lower() or "404" in str(e):
            st.error("❌ README.md file not found")
        else:
            st.error(f"Error reading README.md: {str(e)}")
    
    st.markdown("---")






