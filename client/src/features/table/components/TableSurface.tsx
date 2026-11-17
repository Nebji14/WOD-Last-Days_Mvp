/**
 * Table ovale au centre de l'écran : rebord, tapis et cercle intérieur.
 *
 * Son rebord passe derrière les sièges des côtés. Le centre du tapis reste vide :
 * il est réservé aux dés et aux images du MJ.
 */
export function TableSurface() {
  return (
    <div aria-hidden="true" className="absolute inset-x-[190px] top-[204px] bottom-[176px]">
      <div className="absolute inset-0 rounded-[50%] border-[1.5px] border-[rgb(201_176_106/0.33)] bg-[linear-gradient(180deg,#2e1c14_0%,#120a07_100%)] shadow-[0_24px_60px_rgb(0_0_0/0.8)]" />
      <div className="absolute inset-x-[22px] inset-y-5 rounded-[50%] border-2 border-[rgb(0_0_0/0.53)] bg-[radial-gradient(ellipse_at_center,#35251a_0%,#20150e_70%,#140d08_100%)] shadow-[inset_0_6px_30px_rgb(0_0_0/0.67)]" />
      <div className="absolute inset-x-[104px] inset-y-[76px] rounded-[50%] border border-[rgb(201_176_106/0.25)]" />
    </div>
  );
}
