{ pkgs ? import <nixpkgs> { } }:
pkgs.mkShell {
  venvDir = ".venv";
  buildInputs = with pkgs;
    [ bashInteractive nodePackages."@angular/cli" python312 nodejs_22 ]
    ++ (with pkgs.python311Packages; [ pip venvShellHook ]);

  shellHook = ''
    echo "python flake"
  '';
}
